#!/usr/bin/env pwsh
# Build Windows executable with PyInstaller
# Usage: .\scripts\build_windows.ps1 [version]
# Note: Must be run from the repository root directory

param(
    [string]$Version = "1.0.0"
)

Write-Host "Building CooPad for Windows version $Version" -ForegroundColor Green
Write-Host ""

# Check if main.py exists (verify we're in the right directory)
if (-not (Test-Path "main.py")) {
    Write-Host "ERROR: main.py not found. Please run this script from the repository root directory." -ForegroundColor Red
    Write-Host "Example: .\scripts\build_windows.ps1" -ForegroundColor Yellow
    exit 1
}

# Check if spec file exists
if (-not (Test-Path "scripts\coopad.spec")) {
    Write-Host "ERROR: Spec file 'scripts\coopad.spec' not found!" -ForegroundColor Red
    Write-Host "Please ensure the spec file exists in the scripts directory." -ForegroundColor Yellow
    exit 1
}

# Install dependencies
# Note: Using pygame-ce (Community Edition) which supports Python 3.12+
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install pyinstaller pillow pygame-ce vgamepad
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies!" -ForegroundColor Red
    exit 1
}

# Build executable using spec file
Write-Host "Running PyInstaller with spec file..." -ForegroundColor Yellow
Write-Host "Note: The spec file handles proper bundling of vgamepad DLL files" -ForegroundColor Cyan
pyinstaller --noconfirm scripts\coopad.spec

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Build failed! PyInstaller encountered an error." -ForegroundColor Red
    Write-Host "Please check the output above for details." -ForegroundColor Yellow
    exit $LASTEXITCODE
}

# Verify that the executable was actually created
if (-not (Test-Path "dist\coopad.exe")) {
    Write-Host ""
    Write-Host "ERROR: Build completed but executable not found at dist\coopad.exe" -ForegroundColor Red
    Write-Host "Please check the build output for errors." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Build complete!" -ForegroundColor Green
Write-Host "Executable: dist\coopad.exe" -ForegroundColor Cyan
Write-Host ""
Write-Host "To create an installer, you can use:" -ForegroundColor Yellow
Write-Host "- Inno Setup (https://jrsoftware.org/isinfo.php)"
Write-Host "- NSIS (https://nsis.sourceforge.io/)"
Write-Host "- WiX Toolset (https://wixtoolset.org/)"
