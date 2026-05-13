###############################################################
# Build-Portable.ps1
# Crea una distribuzione portabile ZIP di Songpress++
# usando cx_Freeze in un venv dedicato.
#
# Uso:
#   cd "<cartella progetto>"
#   .\installer\Build-Portable.ps1
#
# Output:
#   .\dist\Songpress++-<versione>-portable.zip
###############################################################

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ── Parametri ────────────────────────────────────────────────────────────────

$ProjectRoot = Split-Path -Parent $PSScriptRoot   # padre di installer\
$VenvDir     = Join-Path $ProjectRoot '.venv-build'
$BuildDir    = Join-Path $ProjectRoot 'build'
$DistDir     = Join-Path $ProjectRoot 'dist'

# Legge la versione da pyproject.toml senza dipendenze esterne
$TomlPath    = Join-Path $ProjectRoot 'pyproject.toml'
$VersionLine = Select-String -Path $TomlPath -Pattern '^version\s*=\s*"(.+)"' | Select-Object -First 1
if (-not $VersionLine) { throw "Impossibile leggere la versione da pyproject.toml" }
$Version     = $VersionLine.Matches[0].Groups[1].Value

$ZipName     = "Songpress++-$Version-portable.zip"
$ZipPath     = Join-Path $DistDir $ZipName

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Songpress++ $Version — Build portabile"          -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Progetto : $ProjectRoot"
Write-Host "  Venv     : $VenvDir"
Write-Host "  Output   : $ZipPath"
Write-Host ""

# ── 1. Venv ──────────────────────────────────────────────────────────────────

if (-not (Test-Path $VenvDir)) {
    Write-Host "[1/6] Creazione venv..." -ForegroundColor Yellow
    python -m venv $VenvDir
} else {
    Write-Host "[1/6] Venv esistente, riutilizzo." -ForegroundColor Green
}

$Pip    = Join-Path $VenvDir 'Scripts\pip.exe'
$Python = Join-Path $VenvDir 'Scripts\python.exe'

# ── 2. Dipendenze ────────────────────────────────────────────────────────────

Write-Host "[2/6] Installazione dipendenze (può richiedere alcuni minuti)..." -ForegroundColor Yellow

& $Pip install --upgrade pip --quiet
& $Pip install --quiet `
    cx_Freeze `
    "wxPython>=4.2.4,<5.0.0" `
    "requests>=2.32.4,<3.0.0" `
    "python-pptx>=1.0.2,<2.0.0" `
    "pyshortcuts>=1.9.5,<2.0.0" `
    "reportlab>=4.0.0,<5.0.0" `
    "pypdf>=6.0.0,<7.0.0" `
    "markdown>=3.4,<4.0.0" `
    "mistune>=3.0.0,<4.0.0"

if ($LASTEXITCODE -ne 0) { throw "pip install fallito (codice $LASTEXITCODE)" }
Write-Host "    Dipendenze installate." -ForegroundColor Green

# ── 3. Build cx_Freeze ───────────────────────────────────────────────────────

Write-Host "[3/6] Esecuzione cx_Freeze build_exe..." -ForegroundColor Yellow

Push-Location $ProjectRoot
try {
    & $Python -m cx_Freeze build_exe
    if ($LASTEXITCODE -ne 0) { throw "cx_Freeze fallito (codice $LASTEXITCODE)" }
} finally {
    Pop-Location
}
Write-Host "    Build completata." -ForegroundColor Green

# ── 4. Individua la cartella build prodotta ───────────────────────────────────

# cx_Freeze crea build\exe.<platform>-<pyver>\ o build\<exename>\
$BuildOutput = Get-ChildItem -Path $BuildDir -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $BuildOutput) { throw "Cartella build non trovata in $BuildDir" }
Write-Host "    Cartella build: $($BuildOutput.FullName)"

# ── 5. Copia fonts in templates\fonts (se non già inclusi da cx_Freeze) ──────

Write-Host "[4/6] Verifica cartella templates\fonts..." -ForegroundColor Yellow

$SrcFonts  = Join-Path $ProjectRoot 'src\songpress\templates\fonts'
$DestFonts = Join-Path $BuildOutput.FullName 'templates\fonts'

if (Test-Path $SrcFonts) {
    if (-not (Test-Path $DestFonts)) {
        New-Item -ItemType Directory -Path $DestFonts -Force | Out-Null
    }
    Copy-Item -Path (Join-Path $SrcFonts '*') -Destination $DestFonts -Recurse -Force
    Write-Host "    Font copiati in templates\fonts." -ForegroundColor Green
} else {
    Write-Host "    Nessuna cartella fonts trovata, salto." -ForegroundColor DarkGray
}

# ── 6. Crea ZIP ───────────────────────────────────────────────────────────────

Write-Host "[5/6] Creazione archivio ZIP..." -ForegroundColor Yellow

if (-not (Test-Path $DistDir)) {
    New-Item -ItemType Directory -Path $DistDir -Force | Out-Null
}

if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }

Compress-Archive -Path $BuildOutput.FullName -DestinationPath $ZipPath -CompressionLevel Optimal

$SizeMB = [math]::Round((Get-Item $ZipPath).Length / 1MB, 1)
Write-Host "    ZIP creato: $ZipName ($SizeMB MB)" -ForegroundColor Green

# ── Fine ──────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  COMPLETATO" -ForegroundColor Cyan
Write-Host "  $ZipPath" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Per avviare Songpress++ dalla cartella estratta:" -ForegroundColor White
Write-Host '  .\Songpress++.exe' -ForegroundColor White
Write-Host ""
