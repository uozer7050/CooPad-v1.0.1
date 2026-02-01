#!/usr/bin/env pwsh
# Build Windows executable with PyInstaller
# Usage: .\scripts\build_windows.ps1 [version]

param(
    [string]$Version = "1.0.0"
)

Write-Host "Building CooPad for Windows version $Version" -ForegroundColor Green
Write-Host ""

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install pyinstaller pillow pygame

# Build executable
Write-Host "Running PyInstaller..." -ForegroundColor Yellow
pyinstaller --noconfirm --onefile `
  --name coopad `
  --add-data "img;img" `
  --add-data "gp;gp" `
  --windowed `
  --icon=img\src_CooPad.ico `
  main.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Build complete!" -ForegroundColor Green
    Write-Host "Executable: dist\coopad.exe" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To create an installer, you can use:" -ForegroundColor Yellow
    Write-Host "- Inno Setup (https://jrsoftware.org/isinfo.php)"
    Write-Host "- NSIS (https://nsis.sourceforge.io/)"
    Write-Host "- WiX Toolset (https://wixtoolset.org/)"
} else {
    Write-Host ""
    Write-Host "Build failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}
