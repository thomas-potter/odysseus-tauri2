#Requires -Version 5.1
# Build Odysseus as a portable Windows .exe with a native webview window.
#
# Prerequisites:
#   - Run launch-windows.ps1 once so the venv exists and .env / data/ are ready.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\build-windows-exe.ps1
#   powershell -ExecutionPolicy Bypass -File .\build-windows-exe.ps1 -Clean
#   powershell -ExecutionPolicy Bypass -File .\build-windows-exe.ps1 -Debug
param(
    [switch]$Clean,
    [switch]$Debug
)

$ErrorActionPreference = "Stop"
$Repo = $PSScriptRoot

# Validate venv
$VenvPy = Join-Path $Repo "venv\Scripts\python.exe"
if (-not (Test-Path $VenvPy)) {
    Write-Host "ERROR: venv not found. Please run launch-windows.ps1 first." -ForegroundColor Red
    exit 1
}

Write-Host "=== Odysseus Windows Desktop Build ===" -ForegroundColor Cyan
if ($Debug) {
    Write-Host "DEBUG MODE: console window will remain open so you can see errors." -ForegroundColor Yellow
}

# ── Install build deps ──
Write-Host "Installing pyinstaller + pywebview into venv ..."
& $VenvPy -m pip install --quiet pyinstaller pywebview

# ── Clean old artifacts ──
if ($Clean) {
    Write-Host "Cleaning old build artifacts ..."
    Remove-Item -Recurse -Force "$Repo\build" -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force "$Repo\dist\Odysseus" -ErrorAction SilentlyContinue
}

# ── DEBUG: temporarily flip console=True in the spec ──
$SpecFile = "$Repo\Odysseus.spec"
$OriginalSpec = $null
if ($Debug) {
    $OriginalSpec = Get-Content $SpecFile -Raw
    if ($OriginalSpec -match 'console\s*=\s*False') {
        $FixedSpec = $OriginalSpec -replace 'console\s*=\s*False', 'console = True'
        Set-Content $SpecFile $FixedSpec -NoNewline
        Write-Host "Temporary switch: console = True"
    }
}

# ── Run PyInstaller ──
Write-Host "Running PyInstaller (this may take a few minutes) ..."
& $VenvPy -m PyInstaller "$Repo\Odysseus.spec" --clean --noconfirm
$BuildExit = $LASTEXITCODE

# ── Restore spec if we modified it ──
if ($Debug -and ($null -ne $OriginalSpec)) {
    Set-Content $SpecFile $OriginalSpec -NoNewline
    Write-Host "Restored original Odysseus.spec"
}

if ($BuildExit -ne 0) {
    Write-Host "PyInstaller failed. Scroll up for errors." -ForegroundColor Red
    exit 1
}

# ── Post-build: copy runtime data into _internal (where the app looks when frozen) ──
$Internal = "$Repo\dist\Odysseus\_internal"

if (-not (Test-Path $Internal)) {
    Write-Host "WARNING: _internal folder not found after build. Skipping data copy." -ForegroundColor Yellow
}

if (Test-Path "$Repo\.env") {
    Copy-Item "$Repo\.env" "$Internal\.env" -Force
    Write-Host "Copied existing .env into _internal/"
}
if (Test-Path "$Repo\data") {
    Copy-Item "$Repo\data" "$Internal\data" -Recurse -Force
    Write-Host "Copied existing data/ into _internal/"
}

if (Test-Path "$Repo\dist\Odysseus\desktop.log") {
    Remove-Item "$Repo\dist\Odysseus\desktop.log" -ErrorAction SilentlyContinue
}

# ── Done ──
Write-Host ""
Write-Host "Build complete!" -ForegroundColor Green
Write-Host "  Folder: $Repo\dist\Odysseus"
Write-Host "  Run:    $Repo\dist\Odysseus\Odysseus.exe"
if ($Debug) {
    Write-Host ""
    Write-Host "DEBUG build: run dist\Odysseus\Odysseus.exe from a terminal to see live logs." -ForegroundColor Yellow
}
Write-Host ""
Write-Host "Tip: If the app does not start, use the -Debug switch so the console stays open."
Write-Host "     After it works, rebuild without -Debug for the final windowed version."
Write-Host ""
Write-Host "Share:   Zip the entire dist\Odysseus folder and send it."
