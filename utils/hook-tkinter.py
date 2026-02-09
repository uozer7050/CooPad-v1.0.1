"""
PyInstaller hook for tkinter package.

This hook ensures that all tkinter submodules are properly included
in the PyInstaller bundle. The _tkinter C extension library is handled
separately in the spec file.
"""
from PyInstaller.utils.hooks import collect_submodules

# Collect all tkinter submodules automatically
hiddenimports = collect_submodules('tkinter')
