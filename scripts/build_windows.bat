@echo off
REM Build Windows executable with PyInstaller
REM Usage: scripts\build_windows.bat [version]

set VERSION=%1
if "%VERSION%"=="" set VERSION=1.0.0

echo Building CooPad for Windows version %VERSION%
echo.

REM Install PyInstaller if not present
pip install pyinstaller pillow pygame

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
