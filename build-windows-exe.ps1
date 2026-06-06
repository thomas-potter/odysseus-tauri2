#Requires -Version 5.1
<#
  Build Odysseus as a portable Windows .exe with a native webview window.

  Prerequisites:
    - Run launch-windows.ps1 once so the venv exists and .env / data/ are ready.
    - (Optional) Install Git for Windows if you want full Cookbook support.

  Produces:
    dist/Odysseus/          <-- portable folder; zip this to share
      Odysseus.exe          <-- double-click to run

  Usage:
    powershell -ExecutionPolicy Bypass -File .\build-windows-exe.ps1
    powershell -ExecutionPolicy Bypass -File .\build-windows-exe.ps1 -Clean
#>
param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$repo = $PSScriptRoot

# ── Validate venv ──
$venvPy = Join-Path $repo "venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
    Write-Host "ERROR: venv not found. Please run launch-windows.ps1 first to create it." -ForegroundColor Red
    exit 1
}

Write-Host "=== Odysseus Windows Desktop Build ===" -ForegroundColor Cyan

# ── Install build deps ──
Write-Host "Installing pyinstaller + pywebview into venv …"
& $venvPy -m pip install --quiet pyinstaller pywebview

# ── Clean old artifacts ──
if ($Clean) {
    Write-Host "Cleaning old build artifacts …"
    Remove-Item -Recurse -Force "$repo\build" -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force "$repo\dist\Odysseus" -ErrorAction SilentlyContinue
}

# ── Run PyInstaller ──
Write-Host "Running PyInstaller (this may take a few minutes) …"
& $venvPy -m PyInstaller "$repo\Odysseus.spec" --clean --noconfirm
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller failed. Scroll up for errors." -ForegroundColor Red
    exit 1
}

# ── Post-build: copy runtime files so the folder is self-contained ──
$dist = "$repo\dist\Odysseus"

if (Test-Path "$repo\.env") {
    Copy-Item "$repo\.env" "$dist\.env" -Force
    Write-Host "Copied existing .env into dist/Odysseus/"
}
if (Test-Path "$repo\data") {
    # Merge existing data/ into the dist folder (skip overwrite so user data is safe)
    Copy-Item "$repo\data" "$dist\data" -Recurse -Force
    Write-Host "Copied existing data/ into dist/Odysseus/"
}

# ── Done ──
Write-Host ""
Write-Host "Build complete! ✓" -ForegroundColor Green
Write-Host "  Folder: $dist"
Write-Host "  Run:    $dist\Odysseus.exe"
Write-Host ""
Write-Host "Tip: If the app doesn't start, rebuild with console=True in Odysseus.spec"
Write-Host "     so you can see the server logs in a terminal window."
Write-Host ""
Write-Host "Share:   Zip the entire 'dist\Odysseus' folder and send it."
