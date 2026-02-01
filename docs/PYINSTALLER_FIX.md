# PyInstaller DLL Bundling Fix

## Problem

When building CooPad with PyInstaller on Windows, the application would fail with the following error:

```
FileNotFoundError: Could not find module 'C:\Users\...\AppData\Local\Temp\_MEI...\vgamepad\win\vigem\client\x64\ViGEmClient.dll' (or one of its dependencies).
```

This error occurred because PyInstaller was not automatically detecting and bundling the ViGEmClient.dll files that are required by the vgamepad library.

## Root Cause

The vgamepad library uses ctypes to load the ViGEmClient.dll at runtime. The DLL path is calculated relative to the vgamepad module location:

```python
# From vgamepad/win/vigem_client.py
pathClient = Path(__file__).parent.absolute() / "vigem" / "client" / arch / "ViGEmClient.dll"
vigemClient = CDLL(str(pathClient))
```

When PyInstaller freezes an application:
1. It bundles Python modules into an archive
2. It extracts them to a temporary directory at runtime
3. The `__file__` path changes to point to the temporary extraction location
4. If binary dependencies (DLLs) are not explicitly included, they won't be in the expected location

## Solution

The fix consists of three components:

### 1. PyInstaller Hook (`hook-vgamepad.py`)

This hook tells PyInstaller to collect all data files from the vgamepad package:

```python
from PyInstaller.utils.hooks import collect_data_files
datas = collect_data_files('vgamepad', include_py_files=False)
```

This ensures that the DLL files in `vgamepad/win/vigem/client/` are included in the bundle.

### 2. PyInstaller Spec File (`coopad.spec`)

A custom spec file provides fine-grained control over the build process:

- Explicitly includes the vgamepad data files
- Adds hidden imports for vgamepad modules
- References the custom hook file
- Configures the build for a windowed GUI application

Key sections:
```python
# Collect vgamepad DLLs if on Windows
vgamepad_datas = collect_data_files('vgamepad', include_py_files=False)

# Hidden imports for vgamepad
hiddenimports = [
    'vgamepad',
    'vgamepad.win',
    'vgamepad.win.vigem_client',
    'vgamepad.win.virtual_gamepad',
]

# Use custom hook
Analysis(..., hookspath=['.'], ...)
```

### 3. Updated Build Scripts

The build scripts (`build_windows.ps1` and `build_windows.bat`) now:

1. Install vgamepad as a dependency: `pip install vgamepad`
2. Use the spec file: `pyinstaller coopad.spec`

This replaces the previous inline PyInstaller command that didn't handle binary dependencies.

## Verification

To verify the fix works:

1. Build the executable on Windows:
   ```
   scripts\build_windows.ps1
   ```

2. Check that the DLL files are included in the build:
   ```
   # The DLL should be in the extracted temporary directory when running
   # Or in the dist folder if using --onedir mode
   ```

3. Run the executable and start Host mode - it should initialize vgamepad without errors.

## Benefits

- **Automatic DLL bundling**: No manual file copying required
- **Architecture support**: Handles both x64 and x86 DLL files
- **Maintainable**: Spec file is version-controlled and easy to update
- **Cross-platform**: Spec file handles platform differences gracefully

## Related Files

- `hook-vgamepad.py` - PyInstaller hook for vgamepad
- `coopad.spec` - Main PyInstaller specification file
- `scripts/build_windows.ps1` - PowerShell build script
- `scripts/build_windows.bat` - Batch build script

## Testing Notes

Since the fix requires:
1. Windows operating system
2. vgamepad package installed
3. ViGEm Bus Driver installed

Full testing should be performed on a Windows machine. The fix is designed to gracefully handle cases where vgamepad is not installed (e.g., on Linux).

## References

- PyInstaller documentation: https://pyinstaller.readthedocs.io/
- PyInstaller hooks: https://pyinstaller.readthedocs.io/en/stable/hooks.html
- vgamepad library: https://github.com/yannbouteiller/vgamepad
- ViGEm Bus Driver: https://github.com/ViGEm/ViGEmBus
