# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for CooPad - Remote Gamepad Application

This spec file handles the proper bundling of all dependencies including:
- vgamepad DLL files (Windows only)
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

# Get project root directory
# When PyInstaller runs the spec file, it runs from the directory where pyinstaller is invoked
# which should be the project root, so we use current working directory
project_root = os.getcwd()

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

# Application data files (use absolute paths)
app_datas = [
    (os.path.join(project_root, 'img'), 'img'),  # Include all image assets
    (os.path.join(project_root, 'gp'), 'gp'),    # Include gp package
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

a = Analysis(
    [os.path.join(project_root, 'main.py')],  # Path to main.py from project root
    pathex=[project_root],  # Add project root to path
    binaries=[],
    datas=all_datas,
    hiddenimports=hiddenimports,
    hookspath=[os.path.join(project_root, 'utils')],  # Path to utils from project root
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Icon path for the executable (Windows .ico file)
icon_path = os.path.join(project_root, 'img/src_CooPad.ico')

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
    # Icon path using absolute path from project root
    icon=icon_path if os.path.exists(icon_path) else None,
)
