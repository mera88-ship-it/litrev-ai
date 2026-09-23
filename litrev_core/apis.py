"""
litrev_core.apis — Clientes de APIs académicas (OpenAlex, Semantic
Scholar, Unpaywall) con reintentos y backoff.

Mejoras sobre las versiones previas:
  - reintentos con backoff exponencial (antes fallaba al primer error),
  - extracción de país de afiliación en OpenAlex (antes era "no disponible"),
  - filtros y límites leídos de config, no hardcodeados.
"""
from __future__ import annotations

import logging
import time
from typing import Optional

import requests

OPENALEX_WORKS = "https://api.openalex.org/works"
SS_SEARCH = "https://api.semanticscholar.org/graph/v1/paper/search"
UNPAYWALL = "https://api.unpaywall.org/v2/"

# Mapa parcial de códigos ISO-3166 → nombre (los más frecuentes). Para el
# resto se devuelve el código de dos letras (mejor que "no disponible").
_PAISES = {
    "US": "Estados Unidos", "GB": "Reino Unido", "CA": "Canadá", "AU": "Australia",
    "CN": "China", "IN": "India", "ES": "España", "MX": "México", "BR": "Brasil",
    "DE": "Alemania", "FR": "Francia", "IT": "Italia", "NL": "Países Bajos",
    "SE": "Suecia", "CH": "Suiza", "JP": "Japón", "KR": "Corea del Sur",
    "TR": "Turquía", "IR": "Irán", "ID": "Indonesia", "AR": "Argentina",
    "CL": "Chile", "CO": "Colombia", "PT": "Portugal", "BE": "Bélgica",
    "NO": "Noruega", "DK": "Dinamarca", "FI": "Finlandia", "AT": "Austria",
    "PL": "Polonia", "ZA": "Sudáfrica", "NZ": "Nueva Zelanda", "IE": "Irlanda",
}


def _get(url: str, *, params=None, headers=None, timeout: int = 30,
         intentos: int = 3, logger: Optional[logging.Logger] = None):
    """GET con reintentos y backoff exponencial. Devuelve Response o None."""
    espera = 2.0
    for intento in range(1, intentos + 1):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=timeout)
            if resp.status_code == 429 or resp.status_code >= 500:
                raise requests.RequestException(f"HTTP {resp.status_code}")
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            if logger:
                logger.info(f"    intento {intento}/{intentos} falló: {e}")
            if intento < intentos:
                time.sleep(espera)
                espera *= 2
    return None


def reconstruir_abstract_invertido(work: dict) -> str:
    inv = work.get("abstract_inverted_index")
    if not inv:
        return ""
    posiciones = [(pos, palabra) for palabra, ps in inv.items() for pos in ps]
    posiciones.sort()
    return " ".join(p for _, p in posiciones)


def pais_openalex(work: dict) -> str:
    """País de afiliación más frecuente entre las autorías. '' si no hay."""
    conteo: dict[str, int] = {}
    for authorship in work.get("authorships", []):
        for inst in authorship.get("institutions", []) or []:
            code = (inst.get("country_code") or "").upper()
            if code:
                conteo[code] = conteo.get(code, 0) + 1
        for code in authorship.get("countries", []) or []:
            code = (code or "").upper()
            if code:
                conteo[code] = conteo.get(code, 0) + 1
    if not conteo:
        return ""
    code = max(conteo, key=conteo.get)
    return _PAISES.get(code, code)


def buscar_openalex(queries, max_por_query, filtros, email, api_key,
                    logger: logging.Logger):
    logger.info("\n=== OpenAlex ===")
    if not queries:
        logger.info("  Sin queries. Configurar openalex.queries en config/busqueda.yaml.")
        return []

    tipos = filtros.get("tipos_openalex") or ["article", "review-article", "book-chapter"]
    anio_min = filtros.get("anio_minimo")
    filtro = f"type:{'|'.join(tipos)}"
    if anio_min:
        filtro = f"from_publication_date:{anio_min}-01-01,{filtro}"

    articulos = []
    for i, query in enumerate(queries, 1):
        logger.info(f"\n  Query {i}/{len(queries)}: {str(query)[:60]}...")
        params = {
            "search": query,
            "filter": filtro,
            "sort": "relevance_score:desc",
            "per_page": max_por_query,
            "mailto": email,
        }
        if api_key:
            params["api_key"] = api_key

        resp = _get(OPENALEX_WORKS, params=params, logger=logger)
        if resp is None:
            logger.info("    ERROR: sin respuesta tras reintentos.")
            continue
        data = resp.json()
        results = data.get("results", [])
        logger.info(f"    En API: {data.get('meta', {}).get('count', '?')} | recuperados: {len(results)}")

        for work in results:
            doi = work.get("doi", "") or ""
            if doi.startswith("https://doi.org/"):
                doi = doi.replace("https://doi.org/", "")
            oa = work.get("open_access", {}) or {}
            pdf_url = oa.get("oa_url", "")
            best = work.get("best_oa_location") or {}
            if not pdf_url:
                pdf_url = best.get("pdf_url", "") or best.get("landing_page_url", "")

            articulos.append({
                "fuente_api": "openalex",
                "openalex_id": work.get("id", ""),
                "doi": doi,
                "titulo": work.get("title", "") or "",
                "autores": [a.get("author", {}).get("display_name", "")
                            for a in work.get("authorships", [])],
                "anio": work.get("publication_year"),
                "revista": ((work.get("primary_location") or {}).get("source") or {}).get("display_name", ""),
                "tipo": work.get("type", ""),
                "idioma": work.get("language", "") or "",
                "pais": pais_openalex(work),
                "citaciones": work.get("cited_by_count", 0),
                "is_oa": oa.get("is_oa", False),
                "pdf_url": pdf_url,
                "abstract": work.get("abstract") or reconstruir_abstract_invertido(work),
                "relevance_score": work.get("relevance_score"),
                "query_origen": f"OA_{i}",
            })
        time.sleep(0.5)

    logger.info(f"\n  Total OpenAlex: {len(articulos)}")
    return articulos


def buscar_semantic_scholar(queries, max_por_query, anio_minimo, api_key,
                            logger: logging.Logger):
    logger.info("\n=== Semantic Scholar ===")
    if not queries:
        logger.info("  Sin queries. Configurar semantic_scholar.queries en config/busqueda.yaml.")
        return []

    headers = {"x-api-key": api_key} if api_key else {}
    fields = ("paperId,externalIds,title,authors,year,venue,publicationTypes,"
              "openAccessPdf,abstract,citationCount,journal")
    articulos = []

    for i, query in enumerate(queries, 1):
        logger.info(f"\n  Query {i}/{len(queries)}: {str(query)[:60]}...")
        params = {"query": query, "limit": max_por_query, "fields": fields}
        if anio_minimo:
            params["year"] = f"{anio_minimo}-"
        resp = _get(SS_SEARCH, params=params, headers=headers, logger=logger)
        if resp is None:
            logger.info("    ERROR: sin respuesta tras reintentos.")
            continue
        data = resp.json()
        papers = data.get("data", []) or []
        logger.info(f"    En API: {data.get('total', '?')} | recuperados: {len(papers)}")

        for paper in papers:
            doi = (paper.get("externalIds") or {}).get("DOI", "") or ""
            oa_pdf = paper.get("openAccessPdf") or {}
            journal = paper.get("journal") or {}
            articulos.append({
                "fuente_api": "semantic_scholar",
                "semantic_scholar_id": paper.get("paperId", ""),
                "doi": doi,
                "titulo": paper.get("title", "") or "",
                "autores": [a.get("name", "") for a in (paper.get("authors") or [])],
                "anio": paper.get("year"),
                "revista": journal.get("name", "") or paper.get("venue", ""),
                "tipo": ", ".join(paper.get("publicationTypes") or []),
                "idioma": "",
                "pais": "",
                "citaciones": paper.get("citationCount", 0),
                "is_oa": bool(oa_pdf.get("url")),
                "pdf_url": oa_pdf.get("url", ""),
                "abstract": paper.get("abstract", "") or "",
                "relevance_score": None,
                "query_origen": f"SS_{i}",
            })
        time.sleep(1)

    logger.info(f"\n  Total Semantic Scholar: {len(articulos)}")
    return articulos


def buscar_unpaywall(doi: str, email: str, logger: Optional[logging.Logger] = None) -> str:
    if not doi or not email:
        return ""
    resp = _get(UNPAYWALL + doi, params={"email": email}, timeout=15,
                intentos=2, logger=logger)
    if resp is None:
        return ""
    try:
        best = resp.json().get("best_oa_location") or {}
    except ValueError:
        return ""
    return best.get("url_for_pdf", "") or best.get("url_for_landing_page", "")


def enriquecer_con_unpaywall(articulos, email, logger: logging.Logger):
    logger.info("\n=== Unpaywall (enriquecimiento) ===")
    encontrados = 0
    for art in articulos:
        if art.get("pdf_url") or not art.get("doi"):
            continue
        pdf = buscar_unpaywall(art["doi"], email, logger=logger)
        if pdf:
            art["pdf_url"] = pdf
            art["is_oa"] = True
            encontrados += 1
        time.sleep(0.5)
    logger.info(f"  PDFs encontrados vía Unpaywall: {encontrados}")
    return encontrados
