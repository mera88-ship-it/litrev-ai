"""
litrev_core.descarga — Recuperación de PDFs en cascada multi-fuente.

Prueba una cadena ordenada de fuentes de acceso abierto legal y se queda
con la primera que entrega un PDF válido.

Cada resolver: (art, ctx) -> URL de PDF o None. El descargador valida que
sea un PDF real (bytes %PDF) y supere el tamaño mínimo. Un "libro de
descargas" (descargas.json) registra por candidato el estado y la fuente
que funcionó, lo que permite reanudar y reintentar solo los fallos.

Fuentes y requisitos:
  unpaywall, openalex_meta, europepmc, pmc, arxiv, biorxiv, doaj,
  crossref           → gratis, sin registro (salvo email que ya tienes)
  core               → requiere CORE_API_KEY en .env (registro gratuito)
"""
from __future__ import annotations

import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Callable, Optional

import requests

from litrev_core.io import cargar_json, guardar_json

UA = "LITREV-AI/3.0 (research; mailto:%s)"


@dataclass
class Contexto:
    cred: dict
    cfg_descarga: dict
    logger: logging.Logger
    session: requests.Session = field(default_factory=requests.Session)


def _get(ctx, url, **kw):
    kw.setdefault("timeout", 15)
    kw.setdefault("headers", {"User-Agent": UA % ctx.cred.get("unpaywall_email", "")})
    try:
        return ctx.session.get(url, **kw)
    except requests.RequestException:
        return None


# ── Resolvers (devuelven URL de PDF o None) ──────────────────────
def r_openalex_meta(art, ctx):
    """URL ya recogida en la búsqueda (OpenAlex / Semantic Scholar)."""
    return art.get("pdf_url") or None


def r_unpaywall(art, ctx):
    doi, email = art.get("doi"), ctx.cred.get("unpaywall_email", "")
    if not doi or not email:
        return None
    r = _get(ctx, f"https://api.unpaywall.org/v2/{doi}", params={"email": email})
    if not r or r.status_code != 200:
        return None
    best = (r.json() or {}).get("best_oa_location") or {}
    return best.get("url_for_pdf") or None


def r_europepmc(art, ctx):
    doi = art.get("doi")
    if not doi:
        return None
    r = _get(ctx, "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
             params={"query": f'DOI:"{doi}"', "format": "json", "resultType": "core"})
    if not r or r.status_code != 200:
        return None
    results = ((r.json() or {}).get("resultList") or {}).get("result") or []
    for res in results:
        for u in (res.get("fullTextUrlList") or {}).get("fullTextUrl", []):
            if u.get("documentStyle") == "pdf" and u.get("availability") in ("Open access", "Free"):
                return u.get("url")
        pmcid = res.get("pmcid")
        if pmcid and res.get("isOpenAccess") == "Y":
            return f"https://europepmc.org/articles/{pmcid}?pdf=render"
    return None


def r_pmc(art, ctx):
    """DOI → PMCID (NCBI idconv) → render PDF de Europe PMC (más estable que NCBI)."""
    doi = art.get("doi")
    if not doi:
        return None
    r = _get(ctx, "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/",
             params={"ids": doi, "format": "json", "tool": "litrev-ai",
                     "email": ctx.cred.get("unpaywall_email", "")})
    if not r or r.status_code != 200:
        return None
    recs = (r.json() or {}).get("records") or []
    for rec in recs:
        if rec.get("pmcid"):
            return f"https://europepmc.org/articles/{rec['pmcid']}?pdf=render"
    return None


def r_arxiv(art, ctx):
    doi, titulo = art.get("doi") or "", art.get("titulo") or ""
    # DOI de arXiv directo
    m = re.search(r"(?:arxiv[.:/]|10\.48550/arxiv\.)\s*([0-9]{4}\.[0-9]{4,5})", doi, re.I)
    if m:
        return f"https://arxiv.org/pdf/{m.group(1)}.pdf"
    if len(titulo) < 15:
        return None
    r = _get(ctx, "http://export.arxiv.org/api/query",
             params={"search_query": f'ti:"{titulo}"', "max_results": 1})
    if not r or r.status_code != 200:
        return None
    id_m = re.search(r"<id>(https?://arxiv\.org/abs/([^<]+))</id>", r.text)
    tit_m = re.search(r"<entry>.*?<title>(.*?)</title>", r.text, re.S)
    if not id_m or not tit_m:
        return None
    if SequenceMatcher(None, titulo.lower(), tit_m.group(1).strip().lower()).ratio() < 0.9:
        return None
    return f"https://arxiv.org/pdf/{id_m.group(2).strip()}.pdf"


def r_biorxiv(art, ctx):
    doi = art.get("doi")
    if not doi or "10.1101" not in doi:
        return None
    for servidor in ("biorxiv", "medrxiv"):
        r = _get(ctx, f"https://api.biorxiv.org/details/{servidor}/{doi}")
        if not r or r.status_code != 200:
            continue
        col = (r.json() or {}).get("collection") or []
        if col:
            ver = col[-1].get("version", "1")
            host = "www.biorxiv.org" if servidor == "biorxiv" else "www.medrxiv.org"
            return f"https://{host}/content/{doi}v{ver}.full.pdf"
    return None


def r_doaj(art, ctx):
    doi = art.get("doi")
    if not doi:
        return None
    r = _get(ctx, f"https://doaj.org/api/search/articles/doi:{doi}")
    if not r or r.status_code != 200:
        return None
    for res in (r.json() or {}).get("results", []):
        for link in (res.get("bibjson") or {}).get("link", []):
            if link.get("type") == "fulltext" and "pdf" in (link.get("content_type") or "").lower():
                return link.get("url")
    return None


def r_crossref(art, ctx):
    doi = art.get("doi")
    if not doi:
        return None
    r = _get(ctx, f"https://api.crossref.org/works/{doi}")
    if not r or r.status_code != 200:
        return None
    for link in ((r.json() or {}).get("message") or {}).get("link", []):
        if "pdf" in (link.get("content-type") or "").lower():
            return link.get("URL")
    return None


def r_core(art, ctx):
    key = ctx.cred.get("core_api_key", "")
    doi = art.get("doi")
    if not key or not doi:
        return None
    r = _get(ctx, "https://api.core.ac.uk/v3/search/works",
             params={"q": f'doi:"{doi}"', "limit": 1},
             headers={"Authorization": f"Bearer {key}",
                      "User-Agent": UA % ctx.cred.get("unpaywall_email", "")})
    if not r or r.status_code != 200:
        return None
    for res in (r.json() or {}).get("results", []):
        if res.get("downloadUrl"):
            return res["downloadUrl"]
    return None


RESOLVERS: dict[str, Callable] = {
    "openalex_meta": r_openalex_meta, "unpaywall": r_unpaywall,
    "europepmc": r_europepmc, "pmc": r_pmc, "arxiv": r_arxiv,
    "biorxiv": r_biorxiv, "doaj": r_doaj, "crossref": r_crossref,
    "core": r_core,
}

# ── Descarga y validación ────────────────────────────────────────
def _es_pdf(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            return f.read(5) == b"%PDF-"
    except OSError:
        return False


def descargar(ctx, url, destino: Path, min_kb: int) -> bool:
    headers = {"User-Agent": UA % ctx.cred.get("unpaywall_email", "")}
    try:
        r = ctx.session.get(url, headers=headers, timeout=60, stream=True)
        r.raise_for_status()
        with open(destino, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    except (requests.RequestException, OSError) as e:
        ctx.logger.info(f"    error de descarga: {e}")
        if destino.exists():
            destino.unlink()
        return False
    size_kb = destino.stat().st_size / 1024
    if size_kb < min_kb or not _es_pdf(destino):
        ctx.logger.info(f"    inválido: {size_kb:.0f} KB / pdf={_es_pdf(destino)}")
        destino.unlink(missing_ok=True)
        return False
    ctx.logger.info(f"    OK: {size_kb:.0f} KB")
    return True


def recuperar_articulo(art, ctx, orden, pdf_dir: Path, min_kb: int) -> dict:
    aid = art.get("id_candidato", "")
    destino = pdf_dir / f"{aid}.pdf"
    if destino.exists() and _es_pdf(destino):
        return {"estado": "ok", "fuente": "ya_existia"}
    for nombre in orden:
        resolver = RESOLVERS.get(nombre)
        if resolver is None:
            continue
        try:
            url = resolver(art, ctx)
        except Exception as e:  # noqa: BLE001 — resolver de terceros; degradar y seguir
            ctx.logger.info(f"    [{nombre}] error: {e}")
            url = None
        if url and descargar(ctx, url, destino, min_kb):
            return {"estado": "ok", "fuente": nombre}
    return {"estado": "no_encontrado", "fuente": ""}


def descargar_corpus(articulos, ctx, paths, min_kb, workers=4) -> dict:
    """Recupera el corpus en paralelo, con libro de descargas y reanudación."""
    pdf_dir = paths.pdf_dir
    pdf_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = paths.candidatos_dir / "descargas.json"
    ledger = cargar_json(ledger_path) if ledger_path.exists() else {}

    # Orden de fuentes (solo las habilitadas)
    cfg = ctx.cfg_descarga
    orden = cfg.get("fuentes_orden") or list(RESOLVERS)
    orden = [n for n in orden if n in RESOLVERS]
    if "core" in orden and not ctx.cred.get("core_api_key"):
        orden = [n for n in orden if n != "core"]
    ctx.logger.info(f"Cadena de fuentes: {' → '.join(orden)}")

    pendientes = [a for a in articulos
                  if ledger.get(a.get("id_candidato", ""), {}).get("estado") != "ok"]
    ctx.logger.info(f"Pendientes: {len(pendientes)} / {len(articulos)} (workers={workers})")

    resumen = {"ok": 0, "no_encontrado": 0, "por_fuente": {}}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futuros = {ex.submit(recuperar_articulo, a, ctx, orden, pdf_dir, min_kb): a
                   for a in pendientes}
        for fut in as_completed(futuros):
            art = futuros[fut]
            aid = art.get("id_candidato", "")
            res = fut.result()
            ledger[aid] = {**res, "doi": art.get("doi", ""), "prioridad": art.get("prioridad", "")}
            resumen[res["estado"]] = resumen.get(res["estado"], 0) + 1
            if res["estado"] == "ok":
                resumen["por_fuente"][res["fuente"]] = resumen["por_fuente"].get(res["fuente"], 0) + 1
            ctx.logger.info(f"  [{res['estado']:<13}] {aid} ({res['fuente']})")

    guardar_json(ledger_path, ledger)
    return resumen
