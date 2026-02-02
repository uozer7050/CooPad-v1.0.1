#!/usr/bin/env bash
set -euo pipefail

# Comprehensive build script for creating distribution-ready packages
# Usage: ./scripts/build_all.sh [version]

VERSION=${1:-1.0.0}
BUILD_DIR=$(pwd)
DIST_DIR=${BUILD_DIR}/dist
RELEASES_DIR=${BUILD_DIR}/scripts/releases

echo "═══════════════════════════════════════════════════════"
echo "CooPad Build System - Version ${VERSION}"
echo "═══════════════════════════════════════════════════════"
echo ""

# Ensure we're in project root
if [ ! -f "main.py" ]; then
    echo "Error: main.py not found. Please run from project root."
    exit 1
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf ${BUILD_DIR}/build ${BUILD_DIR}/package
mkdir -p ${DIST_DIR}
mkdir -p ${RELEASES_DIR}
echo "✓ Build directories cleaned"
echo ""

# Detect platform
echo "Detecting platform..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="Linux"
    echo "✓ Detected: ${PLATFORM}"
    echo ""
    echo "Building for Linux..."
    echo "───────────────────────────────────────────────────────"
    ./scripts/build_deb.sh ${VERSION}
    echo "───────────────────────────────────────────────────────"
    echo "✓ Linux .deb package created"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    PLATFORM="Windows"
    echo "✓ Detected: ${PLATFORM}"
    echo ""
    echo "Building for Windows..."
    echo "───────────────────────────────────────────────────────"
    # Call Windows build script
    if [ -f "scripts/build_windows.bat" ]; then
        cmd /c scripts\\build_windows.bat ${VERSION}
    elif [ -f "scripts/build_windows.ps1" ]; then
        powershell -ExecutionPolicy Bypass -File scripts/build_windows.ps1 -Version ${VERSION}
    else
        echo "Error: Windows build script not found"
        exit 1
    fi
    echo "───────────────────────────────────────────────────────"
    echo "✓ Windows executable created"
else
    echo "⚠ Unknown platform: $OSTYPE"
    echo "Supported platforms: Linux (linux-gnu), Windows (msys/win32/cygwin)"
    echo ""
    echo "Please run platform-specific build script manually:"
    echo "  Linux:   ./scripts/build_deb.sh ${VERSION}"
    echo "  Windows: scripts\\build_windows.bat ${VERSION}"
    exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo "✓ Build Complete!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "Platform: ${PLATFORM}"
echo "Version:  ${VERSION}"
echo ""
echo "Output directories:"
echo "  Distribution: ${DIST_DIR}"
echo "  Releases:     ${RELEASES_DIR}"
echo ""

# List build artifacts
if [ -d "${DIST_DIR}" ] && [ "$(ls -A ${DIST_DIR} 2>/dev/null)" ]; then
    echo "Distribution files:"
    ls -lh ${DIST_DIR}/ 2>/dev/null || dir ${DIST_DIR} 2>/dev/null || true
    echo ""
fi

if [ -d "${RELEASES_DIR}" ] && [ "$(ls -A ${RELEASES_DIR} 2>/dev/null)" ]; then
    echo "Release files:"
    ls -lh ${RELEASES_DIR}/ 2>/dev/null || dir ${RELEASES_DIR} 2>/dev/null || true
    echo ""
fi

echo "Next steps:"
echo "  1. Test the build on a clean system"
echo "  2. Verify all dependencies are bundled correctly"
echo "  3. Create GitHub release with version ${VERSION}"
echo "  4. Upload distribution files from ${RELEASES_DIR}"
echo ""

exit 0
