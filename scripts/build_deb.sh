#!/usr/bin/env bash
set -euo pipefail

# Build a single-file PyInstaller binary and package it into a .deb
# Usage: ./scripts/build_deb.sh [version]

VERSION=${1:-1.0.0}
PKGNAME=coopad
BUILD_DIR=$(pwd)
DIST_DIR=${BUILD_DIR}/dist
PKG_DIR=${BUILD_DIR}/package

echo "Building ${PKGNAME} version ${VERSION}"

# Ensure venv activated or use system python
if [ -z "${VIRTUAL_ENV:-}" ]; then
  echo "Warning: virtualenv not active. It's recommended to activate your venv before building."
fi

echo "Installing build deps and runtime dependencies..."
pip install --upgrade pyinstaller Pillow pygame-ce evdev >/dev/null

echo "Running PyInstaller..."
pyinstaller --noconfirm --onefile \
  --name ${PKGNAME} \
  --add-data "img:img" \
  --add-data "gp:gp" \
  --hidden-import=evdev \
  --collect-all=evdev \
  main.py

echo "Preparing package tree..."
rm -rf ${PKG_DIR}
mkdir -p ${PKG_DIR}/DEBIAN
mkdir -p ${PKG_DIR}/usr/bin
mkdir -p ${PKG_DIR}/usr/share/applications
mkdir -p ${PKG_DIR}/usr/share/pixmaps
mkdir -p ${PKG_DIR}/usr/share/doc/${PKGNAME}
mkdir -p ${PKG_DIR}/etc/udev/rules.d

echo "Copying binary, icon, and docs..."
cp ${DIST_DIR}/${PKGNAME} ${PKG_DIR}/usr/bin/${PKGNAME}
cp img/src_CooPad.png ${PKG_DIR}/usr/share/pixmaps/${PKGNAME}.png || true
cp README.md ${PKG_DIR}/usr/share/doc/${PKGNAME}/README.md || true

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

# Create postinst script to set up permissions and install evdev
cat > ${PKG_DIR}/DEBIAN/postinst <<'POSTINST'
#!/bin/bash
set -e

# Reload udev rules
if command -v udevadm >/dev/null 2>&1; then
    udevadm control --reload-rules
    udevadm trigger
fi

# Create input group if it doesn't exist
if ! getent group input >/dev/null 2>&1; then
    groupadd -r input
fi

# Load uinput module if not already loaded
if ! lsmod | grep -q uinput; then
    modprobe uinput || true
fi

# Install python3-evdev if available via apt
# This runs as root during package installation
if command -v apt-get >/dev/null 2>&1; then
    apt-get update -qq >/dev/null 2>&1 || true
    apt-get install -y -qq python3-evdev >/dev/null 2>&1 || true
fi

# Try to install evdev system-wide via pip as fallback (without --user since we're root)
if command -v pip3 >/dev/null 2>&1; then
    pip3 install -q evdev >/dev/null 2>&1 || true
fi

echo "CooPad installed successfully!"
echo "To use Host mode, add your user to the 'input' group:"
echo "  sudo usermod -aG input \$USER"
echo "Then log out and back in for changes to take effect."

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
Depends: python3
Recommends: python3-pip, python3-evdev
Maintainer: CooPad <no-reply@example.com>
Description: CooPad remote gamepad (host/client)
 Cross-platform remote gamepad application that allows you to use a
 gamepad over the network. A client captures gamepad inputs and sends
 them to a host, which creates a virtual gamepad that games can use.
 .
 Features:
  - Cross-platform support (Windows and Linux)
  - Low latency gameplay
  - Configurable update rates (30/60/90 Hz)
  - Real-time network statistics
  - Automatic platform detection
  - Automatic dependency installation
EOF

# Set permissions
chmod -R 0755 ${PKG_DIR}/usr/bin/${PKGNAME} || true
chmod 0644 ${PKG_DIR}/etc/udev/rules.d/99-coopad-uinput.rules
chmod 0644 ${PKG_DIR}/usr/share/applications/${PKGNAME}.desktop || true
chmod 0644 ${PKG_DIR}/usr/share/pixmaps/${PKGNAME}.png || true

echo "Building .deb package..."
DEBFILE=${DIST_DIR}/${PKGNAME}_${VERSION}_amd64.deb
dpkg-deb --build ${PKG_DIR} ${DEBFILE}

echo "Package created: ${DEBFILE}"
echo ""
echo "To install:"
echo "  sudo dpkg -i ${DEBFILE}"
echo ""
echo "To run:"
echo "  coopad"
echo ""
echo "Or from menu: Applications > Games > CooPad"

exit 0
