# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for CooPad - Remote Gamepad Application

This spec file handles the proper bundling of all dependencies including:
- vgamepad DLL files (Windows only)
- evdev module (Linux only)
- Image assets
- Python packages

Usage:
    pyinstaller scripts/coopad.spec
    (run from project root directory)
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Determine platform
is_windows = sys.platform == 'win32'
is_linux = sys.platform.startswith('linux')

# Collect vgamepad data files (DLLs) if on Windows
vgamepad_datas = []
if is_windows:
    try:
        # Try to collect vgamepad data files
        vgamepad_datas = collect_data_files('vgamepad', include_py_files=False)
        print(f"Found {len(vgamepad_datas)} vgamepad data files")
    except Exception as e:
        print(f"Warning: Could not collect vgamepad data files: {e}")
        print("vgamepad may not be installed. Install with: pip install vgamepad")

# Collect evdev data files if on Linux
evdev_datas = []
if is_linux:
    try:
        evdev_datas = collect_data_files('evdev', include_py_files=False)
        print(f"Found {len(evdev_datas)} evdev data files")
    except Exception as e:
        print(f"Warning: Could not collect evdev data files: {e}")

# Application data files
app_datas = [
    ('img', 'img'),  # Include all image assets
    ('gp', 'gp'),    # Include gp package
]

# Combine all data files
all_datas = app_datas + vgamepad_datas + evdev_datas

# Hidden imports that PyInstaller might miss
hiddenimports = [
    'PIL',
    'PIL._imagingtk',
    'PIL._tkinter_finder',
    'tkinter',
    'tkinter.ttk',
    'queue',
    'logging',
    'socket',
    'threading',
]

# Add platform-specific hidden imports
if is_windows:
    hiddenimports.extend([
        'vgamepad',
        'vgamepad.win',
        'vgamepad.win.vigem_client',
        'vgamepad.win.virtual_gamepad',
    ])
elif is_linux:
    hiddenimports.extend([
        'evdev',
        'evdev.ecodes',
        'evdev.events',
        'evdev.uinput',
    ])

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=all_datas,
    hiddenimports=hiddenimports,
    hookspath=['utils'],  # Look for hooks in utils directory
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='coopad',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (GUI application)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Icon path is relative to where pyinstaller is run (project root)
    # The build scripts ensure this is run from the correct directory
    icon='img/src_CooPad.ico' if os.path.exists('img/src_CooPad.ico') else None,
)
