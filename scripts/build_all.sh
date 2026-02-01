#!/usr/bin/env bash
set -euo pipefail

# Comprehensive build script for creating distribution-ready packages
# Usage: ./scripts/build_all.sh [version]

VERSION=${1:-1.0.0}
BUILD_DIR=$(pwd)
DIST_DIR=${BUILD_DIR}/dist

echo "═══════════════════════════════════════════════════════"
echo "CooPad Build System - Version ${VERSION}"
echo "═══════════════════════════════════════════════════════"
echo ""

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf ${BUILD_DIR}/build ${BUILD_DIR}/package ${BUILD_DIR}/*.spec
mkdir -p ${DIST_DIR}

# Check platform
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Building for Linux..."
    echo ""
    ./scripts/build_deb.sh ${VERSION}
    echo ""
    echo "✓ Linux .deb package created in dist/"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "Building for Windows..."
    echo ""
    # Call Windows build script
    cmd /c scripts\\build_windows.bat ${VERSION}
    echo ""
    echo "✓ Windows executable created in dist/"
else
    echo "⚠ Unknown platform: $OSTYPE"
    echo "Please run platform-specific build script manually."
    exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo "Build Complete!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "Output directory: ${DIST_DIR}"
ls -lh ${DIST_DIR}/ 2>/dev/null || dir ${DIST_DIR} 2>/dev/null || true
echo ""
echo "Next steps:"
echo "1. Test the build on a clean system"
echo "2. Create GitHub release"
echo "3. Upload distribution files"
echo ""

exit 0
