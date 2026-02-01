"""
Platform detection and compatibility information module.
Provides user-friendly status messages about platform capabilities.
"""
import sys
import platform
import os
import subprocess


class PlatformInfo:
    """Detect platform capabilities and provide user-friendly messages."""
    
    def __init__(self):
        self.os_name = platform.system()
        self.is_windows = sys.platform == 'win32'
        self.is_linux = sys.platform.startswith('linux')
        self.is_macos = sys.platform == 'darwin'
        
        # Check virtual gamepad support
        self._check_capabilities()
    
    def _check_capabilities(self):
        """Check what virtual gamepad capabilities are available."""
        self.vgamepad_available = False
        self.evdev_available = False
        self.uinput_available = False
        self.uinput_accessible = False
        
        # Check for Windows vgamepad
        try:
            import vgamepad
            self.vgamepad_available = True
        except ImportError:
            pass
        
        # Check for Linux evdev - attempt auto-install if missing on Linux
        if self.is_linux:
            try:
                import evdev
                self.evdev_available = True
            except ImportError:
                # Try to auto-install evdev on Linux
                try:
                    # Silently attempt pip install
                    subprocess.check_call(
                        [sys.executable, '-m', 'pip', 'install', '--user', '-q', 'evdev'],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=30
                    )
                    # Try importing again
                    import evdev
                    self.evdev_available = True
                except Exception:
                    # Auto-install failed, evdev remains unavailable
                    self.evdev_available = False
        
        # Check for uinput device (Linux)
        if self.is_linux and os.path.exists('/dev/uinput'):
            self.uinput_available = True
            self.uinput_accessible = os.access('/dev/uinput', os.W_OK)
    
    def get_platform_name(self):
        """Get user-friendly platform name."""
        if self.is_windows:
            return "Windows"
        elif self.is_linux:
            return "Linux"
        elif self.is_macos:
            return "macOS"
        else:
            return self.os_name
    
    def get_host_status(self):
        """Get host capability status with user-friendly message."""
        if self.is_windows:
            if self.vgamepad_available:
                return {
                    'status': 'ready',
                    'icon': '✓',
                    'color': '#22c55e',
                    'message': 'ViGEmBus driver detected - Virtual gamepad ready',
                    'details': 'Your Windows system can create virtual Xbox 360 controllers'
                }
            else:
                return {
                    'status': 'error',
                    'icon': '✗',
                    'color': '#ef4444',
                    'message': 'ViGEmBus driver not found',
                    'details': 'Install ViGEm Bus Driver from github.com/ViGEm/ViGEmBus/releases',
                    'action': 'Download and install ViGEmBus driver to create virtual gamepads'
                }
        elif self.is_linux:
            if self.evdev_available:
                if self.uinput_accessible:
                    return {
                        'status': 'ready',
                        'icon': '✓',
                        'color': '#22c55e',
                        'message': 'uinput device accessible - Virtual gamepad ready',
                        'details': 'Your Linux system can create virtual gamepads via evdev/uinput'
                    }
                elif self.uinput_available:
                    return {
                        'status': 'warning',
                        'icon': '⚠',
                        'color': '#f59e0b',
                        'message': 'uinput device found but not accessible',
                        'details': 'Run: ./scripts/setup_uinput.sh or use sudo',
                        'action': 'Setup uinput permissions to create virtual gamepads without sudo'
                    }
                else:
                    return {
                        'status': 'error',
                        'icon': '✗',
                        'color': '#ef4444',
                        'message': 'uinput device not found',
                        'details': 'Load uinput module: sudo modprobe uinput',
                        'action': 'Enable uinput kernel module to create virtual gamepads'
                    }
            else:
                return {
                    'status': 'warning',
                    'icon': '⚠',
                    'color': '#f59e0b',
                    'message': 'evdev library is being installed automatically',
                    'details': 'The application will set up required dependencies',
                    'action': 'Host mode will be available after installation completes'
                }
        else:
            return {
                'status': 'unsupported',
                'icon': '?',
                'color': '#6b7280',
                'message': 'Platform not fully supported',
                'details': f'{self.os_name} may not support virtual gamepad creation'
            }
    
    def get_client_status(self):
        """Get client capability status with user-friendly message."""
        try:
            import pygame
            pygame_available = True
        except ImportError:
            pygame_available = False
        
        if pygame_available:
            return {
                'status': 'ready',
                'icon': '✓',
                'color': '#22c55e',
                'message': 'pygame detected - Gamepad input ready',
                'details': 'Can capture and send physical gamepad inputs'
            }
        else:
            return {
                'status': 'warning',
                'icon': '⚠',
                'color': '#f59e0b',
                'message': 'pygame not installed',
                'details': 'Install with: pip install pygame',
                'action': 'Install pygame to capture physical gamepad input (optional - can still send test data)'
            }
    
    def get_compatibility_info(self):
        """Get cross-platform compatibility information."""
        host_ok = self.get_host_status()['status'] in ['ready', 'warning']
        client_ok = self.get_client_status()['status'] in ['ready', 'warning']
        
        info = {
            'can_host': host_ok,
            'can_client': client_ok,
            'platform': self.get_platform_name(),
        }
        
        # Cross-platform compatibility notes
        if self.is_windows:
            info['notes'] = [
                'Can receive input from Linux clients',
                'Can receive input from Windows clients',
                'ViGEmBus creates Xbox 360 controllers recognized by all games'
            ]
        elif self.is_linux:
            info['notes'] = [
                'Can receive input from Windows clients',
                'Can receive input from Linux clients',
                'evdev/uinput creates standard Linux joystick devices'
            ]
        
        return info
    
    def get_setup_instructions(self):
        """Get platform-specific setup instructions."""
        if self.is_windows:
            return {
                'host': [
                    '1. Download ViGEmBus installer from GitHub',
                    '2. Run installer with administrator privileges',
                    '3. Restart application after installation',
                    '4. Allow Python through Windows Firewall'
                ],
                'client': [
                    '1. Install pygame: pip install pygame',
                    '2. Connect USB gamepad (optional)',
                    '3. Allow Python through Windows Firewall'
                ]
            }
        elif self.is_linux:
            return {
                'host': [
                    '1. Install evdev: pip install evdev',
                    '2. Load uinput module: sudo modprobe uinput',
                    '3. Setup permissions: ./scripts/setup_uinput.sh',
                    '4. Log out and back in (or use: newgrp input)'
                ],
                'client': [
                    '1. Install pygame: pip install pygame',
                    '2. Connect USB gamepad (optional)'
                ]
            }
        else:
            return {
                'host': ['Platform not fully supported'],
                'client': ['Platform not fully supported']
            }


# Global instance
_platform_info = None

def get_platform_info():
    """Get global platform info instance."""
    global _platform_info
    if _platform_info is None:
        _platform_info = PlatformInfo()
    return _platform_info
