@echo off
REM Build Windows executable with PyInstaller
REM Usage: scripts\build_windows.bat [version]
REM Note: Must be run from the repository root directory

set VERSION=%1
if "%VERSION%"=="" set VERSION=1.0.0

echo Building CooPad for Windows version %VERSION%
echo.

REM Check if main.py exists (verify we're in the right directory)
if not exist "main.py" (
    echo ERROR: main.py not found. Please run this script from the repository root directory.
    echo Example: scripts\build_windows.bat
    pause
    exit /b 1
)

REM Install dependencies
REM Note: Using pygame-ce (Community Edition) which supports Python 3.12+
echo Installing dependencies...
pip install pyinstaller pillow pygame-ce

REM Build executable
echo Running PyInstaller...
pyinstaller --noconfirm --onefile ^
  --name coopad ^
  --add-data "img;img" ^
  --add-data "gp;gp" ^
  --windowed ^
  --icon=img\src_CooPad.ico ^
  main.py

echo.
echo Build complete!
echo Executable: dist\coopad.exe
echo.
echo To create an installer, you can use:
echo - Inno Setup (https://jrsoftware.org/isinfo.php)
echo - NSIS (https://nsis.sourceforge.io/)
echo - WiX Toolset (https://wixtoolset.org/)
echo.
pause
