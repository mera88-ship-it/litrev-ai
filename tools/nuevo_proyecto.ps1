<#
.SYNOPSIS
  Crea un proyecto de revision de literatura nuevo a partir de la plantilla LITREV-AI.

.DESCRIPTION
  Genera un repositorio privado en GitHub desde la plantilla y lo clona en una carpeta propia,
  listo para correr la Fase 0. No toca la plantilla. Requiere gh (GitHub CLI) autenticado.

.PARAMETER Tema
  El tema de la revision (texto libre). Se convierte en un nombre seguro: por ejemplo
  "teletrabajo" -> repo "litrev-teletrabajo".

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\nuevo_proyecto.ps1 "teletrabajo"

.NOTES
  Autenticacion previa (una sola vez):  gh auth login
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string] $Tema,

    # Carpeta raiz donde viven todos los proyectos de revision de literatura.
    [string] $CarpetaProyectos = (Join-Path $env:USERPROFILE 'Documents\proyectos-revision-literatura'),

    # Dueno y plantilla en GitHub.
    [string] $Owner = 'mera88-ship-it',
    [string] $Plantilla = 'mera88-ship-it/litrev-ai'
)

$ErrorActionPreference = 'Stop'

function Resolve-Gh {
    $cmd = Get-Command gh -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $pf = Join-Path $env:ProgramFiles 'GitHub CLI\gh.exe'
    if (Test-Path $pf) { return $pf }
    throw "No se encontro 'gh' (GitHub CLI). Instalalo y ejecuta 'gh auth login'."
}

function ConvertTo-Slug {
    param([string] $Texto)
    # Quita acentos (NFD + descarta marcas), pasa a minusculas y deja solo a-z 0-9 y guiones.
    $norm = $Texto.Normalize([Text.NormalizationForm]::FormD)
    $sb = [Text.StringBuilder]::new()
    foreach ($c in $norm.ToCharArray()) {
        $cat = [Globalization.CharUnicodeInfo]::GetUnicodeCategory($c)
        if ($cat -ne [Globalization.UnicodeCategory]::NonSpacingMark) { [void]$sb.Append($c) }
    }
    $limpio = $sb.ToString().Normalize([Text.NormalizationForm]::FormC).ToLowerInvariant()
    $slug = ($limpio -replace '[^a-z0-9]+', '-').Trim('-')
    if ([string]::IsNullOrWhiteSpace($slug)) { throw "El tema '$Texto' no produce un nombre valido." }
    return $slug
}

$gh = Resolve-Gh
$slug = ConvertTo-Slug -Texto $Tema
$repo = "litrev-$slug"
$destino = Join-Path $CarpetaProyectos $repo

Write-Host "Tema:    $Tema"
Write-Host "Repo:    $Owner/$repo  (privado, desde $Plantilla)"
Write-Host "Carpeta: $destino"
Write-Host ""

# Verificar que gh este autenticado.
& $gh auth status *> $null
if ($LASTEXITCODE -ne 0) { throw "gh no esta autenticado. Ejecuta 'gh auth login' y reintenta." }

if (Test-Path $destino) { throw "Ya existe la carpeta $destino. Elige otro tema o borrala primero." }
if (-not (Test-Path $CarpetaProyectos)) { New-Item -ItemType Directory -Path $CarpetaProyectos | Out-Null }

Write-Host "Creando el repositorio en GitHub..."
& $gh repo create "$Owner/$repo" --private --template $Plantilla
if ($LASTEXITCODE -ne 0) { throw "No se pudo crear el repositorio (revisa si ya existe)." }

Write-Host "Clonando en la carpeta del proyecto..."
& $gh repo clone "$Owner/$repo" "$destino"
if ($LASTEXITCODE -ne 0) { throw "El repo se creo pero no se pudo clonar. Clonalo a mano: gh repo clone $Owner/$repo `"$destino`"" }

Write-Host ""
Write-Host "Proyecto creado correctamente." -ForegroundColor Green
Write-Host "Siguiente paso: abre Claude Code en esta carpeta y corre la Fase 0:"
Write-Host "  $destino"
