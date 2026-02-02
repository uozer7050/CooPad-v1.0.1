#!/usr/bin/env bash
set -euo pipefail

# Build a single-file PyInstaller binary and package it into a .deb
# Usage: ./scripts/build_deb.sh [version]

VERSION=${1:-1.0.0}
PKGNAME=coopad
BUILD_DIR=$(pwd)
DIST_DIR=${BUILD_DIR}/dist
PKG_DIR=${BUILD_DIR}/package
RELEASES_DIR=${BUILD_DIR}/scripts/releases

echo "═══════════════════════════════════════════════════════"
echo "Building ${PKGNAME} version ${VERSION} for Linux"
echo "═══════════════════════════════════════════════════════"
echo ""

# Ensure we're in project root
if [ ! -f "main.py" ]; then
  echo "Error: main.py not found. Please run from project root."
  exit 1
fi

# Ensure venv activated or use system python
if [ -z "${VIRTUAL_ENV:-}" ]; then
  echo "Warning: virtualenv not active. Using system Python."
fi

echo "Installing build dependencies and runtime dependencies..."
pip3 install --upgrade --quiet pyinstaller Pillow pygame-ce evdev 2>/dev/null || \
pip install --upgrade --quiet pyinstaller Pillow pygame-ce evdev

echo "Running PyInstaller with spec file..."
pyinstaller --noconfirm scripts/coopad.spec

echo "Preparing package tree..."
rm -rf ${PKG_DIR}
mkdir -p ${PKG_DIR}/DEBIAN
mkdir -p ${PKG_DIR}/usr/bin
mkdir -p ${PKG_DIR}/usr/share/applications
mkdir -p ${PKG_DIR}/usr/share/pixmaps
mkdir -p ${PKG_DIR}/usr/share/doc/${PKGNAME}
mkdir -p ${PKG_DIR}/etc/udev/rules.d

echo "Copying binary, icon, and docs..."
if [ -f "${DIST_DIR}/${PKGNAME}" ]; then
  cp ${DIST_DIR}/${PKGNAME} ${PKG_DIR}/usr/bin/${PKGNAME}
  chmod 0755 ${PKG_DIR}/usr/bin/${PKGNAME}
else
  echo "Error: Binary ${DIST_DIR}/${PKGNAME} not found!"
  exit 1
fi

# Copy icon if exists
if [ -f "img/src_CooPad.png" ]; then
  cp img/src_CooPad.png ${PKG_DIR}/usr/share/pixmaps/${PKGNAME}.png
  chmod 0644 ${PKG_DIR}/usr/share/pixmaps/${PKGNAME}.png
fi

# Copy README if exists
if [ -f "README.md" ]; then
  cp README.md ${PKG_DIR}/usr/share/doc/${PKGNAME}/README.md
  chmod 0644 ${PKG_DIR}/usr/share/doc/${PKGNAME}/README.md
fi

# Create desktop entry
cat > ${PKG_DIR}/usr/share/applications/${PKGNAME}.desktop <<'DESKTOP'
[Desktop Entry]
Version=1.0
Type=Application
Name=CooPad
Comment=Remote Gamepad over Network
Exec=/usr/bin/coopad
Icon=coopad
Terminal=false
Categories=Game;Utility;Network;
DESKTOP

# Include udev rule so package can install device permissions
cat > ${PKG_DIR}/etc/udev/rules.d/99-coopad-uinput.rules <<'UDEV'
# Allow members of 'input' group to access uinput
KERNEL=="uinput", MODE="0660", GROUP="input"
SUBSYSTEM=="uinput", MODE="0660", GROUP="input"
UDEV

# Create postinst script to set up permissions and load uinput module
cat > ${PKG_DIR}/DEBIAN/postinst <<'POSTINST'
#!/bin/bash
set -e

# Reload udev rules
if command -v udevadm >/dev/null 2>&1; then
    udevadm control --reload-rules 2>/dev/null || true
    udevadm trigger 2>/dev/null || true
fi

# Create input group if it doesn't exist
if ! getent group input >/dev/null 2>&1; then
    groupadd -r input 2>/dev/null || true
fi

# Load uinput module if not already loaded
if ! lsmod | grep -q uinput; then
    modprobe uinput 2>/dev/null || true
fi

# Install python3-evdev if available via apt (suppress output)
if command -v apt-get >/dev/null 2>&1; then
    apt-get update -qq 2>/dev/null || true
    apt-get install -y -qq python3-evdev 2>/dev/null || true
fi

# Try to install evdev system-wide via pip3 as fallback
if command -v pip3 >/dev/null 2>&1; then
    pip3 install -q evdev 2>/dev/null || true
fi

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  CooPad installed successfully!                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "To use Host mode (create virtual gamepad), add your user"
echo "to the 'input' group:"
echo ""
echo "  sudo usermod -aG input \$USER"
echo ""
echo "Then log out and back in for changes to take effect."
echo ""
echo "Run CooPad from the applications menu or with: coopad"
echo ""

exit 0
POSTINST

chmod 0755 ${PKG_DIR}/DEBIAN/postinst

echo "Creating DEBIAN/control..."
cat > ${PKG_DIR}/DEBIAN/control <<EOF
Package: ${PKGNAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: amd64
Depends: python3 (>= 3.8), python3-tk
Recommends: python3-pip, python3-evdev, python3-pygame
Maintainer: CooPad Team <no-reply@coopad.io>
Homepage: https://github.com/uozer7050/v5.1
Description: CooPad - Remote Gamepad over Network
 Cross-platform remote gamepad application that allows you to use a
 gamepad over the network. A client captures gamepad inputs and sends
 them to a host, which creates a virtual gamepad that games can use.
 .
 Features:
  - Cross-platform support (Windows and Linux)
  - Low latency network gameplay
  - Configurable update rates (30/60/90/120 Hz)
  - Real-time network statistics and latency monitoring
  - Automatic platform detection and setup
  - Virtual gamepad creation (Linux: evdev/uinput, Windows: ViGEm)
  - Physical gamepad input capture via pygame
EOF

# Set permissions
chmod 0755 ${PKG_DIR}/DEBIAN/postinst
chmod 0644 ${PKG_DIR}/etc/udev/rules.d/99-coopad-uinput.rules || true
chmod 0644 ${PKG_DIR}/usr/share/applications/${PKGNAME}.desktop || true

echo "Building .deb package..."
DEBFILE=${DIST_DIR}/${PKGNAME}_${VERSION}_amd64.deb
dpkg-deb --build ${PKG_DIR} ${DEBFILE}

# Create releases directory and copy the package
echo "Creating releases directory..."
mkdir -p ${RELEASES_DIR}
cp ${DEBFILE} ${RELEASES_DIR}/

echo ""
echo "═══════════════════════════════════════════════════════"
echo "✓ Package created successfully!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "Package: ${DEBFILE}"
echo "Release: ${RELEASES_DIR}/$(basename ${DEBFILE})"
echo ""
echo "To install:"
echo "  sudo dpkg -i ${DEBFILE}"
echo "  sudo apt-get install -f  # Install dependencies if needed"
echo ""
echo "To run:"
echo "  coopad"
echo ""
echo "Or from menu: Applications > Games > CooPad"
echo ""

exit 0
