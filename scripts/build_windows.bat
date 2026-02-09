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

REM Check if spec file exists
if not exist "scripts\coopad.spec" (
    echo ERROR: Spec file "scripts\coopad.spec" not found!
    echo Please ensure the spec file exists in the scripts directory.
    pause
    exit /b 1
)

REM Install dependencies
REM Note: Using pygame-ce (Community Edition) which supports Python 3.12+
echo Installing dependencies...
pip install pyinstaller pillow pygame-ce vgamepad
if errorlevel 1 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)

REM Build executable using spec file
echo Running PyInstaller with spec file...
echo Note: The spec file handles proper bundling of vgamepad DLL files
pyinstaller --noconfirm scripts\coopad.spec
if errorlevel 1 (
    echo.
    echo ERROR: Build failed! PyInstaller encountered an error.
    echo Please check the output above for details.
    pause
    exit /b 1
)

REM Verify that the executable was actually created
if not exist "dist\coopad.exe" (
    echo.
    echo ERROR: Build completed but executable not found at dist\coopad.exe
    echo Please check the build output for errors.
    pause
    exit /b 1
)

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
