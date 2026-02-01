"""
PyInstaller hook for vgamepad package.

This hook ensures that the ViGEmClient DLL files are properly included
in the PyInstaller bundle when building on Windows.
"""
from PyInstaller.utils.hooks import collect_data_files

# Collect all data files from vgamepad package
# This includes the DLL files in vgamepad/win/vigem/client/
datas = collect_data_files('vgamepad', include_py_files=False)

# The vgamepad package contains:
# - vgamepad/win/vigem/client/x64/ViGEmClient.dll
# - vgamepad/win/vigem/client/x86/ViGEmClient.dll
# These need to be bundled with the application
