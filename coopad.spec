# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for CooPad - Remote Gamepad Application

This spec file handles the proper bundling of all dependencies including:
- vgamepad DLL files (Windows only)
- Image assets
- Python packages

Usage:
    pyinstaller coopad.spec
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Determine if we're building on Windows
is_windows = sys.platform == 'win32'

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

# Application data files
app_datas = [
    ('img', 'img'),  # Include all image assets
    ('gp', 'gp'),    # Include gp package
]

# Combine all data files
all_datas = app_datas + vgamepad_datas

# Hidden imports that PyInstaller might miss
hiddenimports = [
    'PIL',
    'PIL._imagingtk',
    'PIL._tkinter_finder',
    'tkinter',
    'tkinter.ttk',
]

# Add platform-specific hidden imports
if is_windows:
    hiddenimports.extend([
        'vgamepad',
        'vgamepad.win',
        'vgamepad.win.vigem_client',
        'vgamepad.win.virtual_gamepad',
    ])

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=all_datas,
    hiddenimports=hiddenimports,
    hookspath=['utils'],  # Look for hooks in utils directory (hook-vgamepad.py)
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
