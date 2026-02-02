"""
Platform detection and compatibility information module.
Provides user-friendly status messages about platform capabilities.
"""
import sys
import platform


class PlatformInfo:
    """Detect platform capabilities and provide user-friendly messages."""
    
    def __init__(self):
        self.os_name = platform.system()
        self.is_windows = sys.platform == 'win32'
        self.is_macos = sys.platform == 'darwin'
        
        # Check virtual gamepad support
        self._check_capabilities()
    
    def _check_capabilities(self):
        """Check what virtual gamepad capabilities are available."""
        self.vgamepad_available = False
        
        # Check for Windows vgamepad
        try:
            import vgamepad
            self.vgamepad_available = True
        except ImportError:
            pass
    
    def get_platform_name(self):
        """Get user-friendly platform name."""
        if self.is_windows:
            return "Windows"
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
        
        # Platform compatibility notes
        if self.is_windows:
            info['notes'] = [
                'Supports multiple Windows clients',
                'ViGEmBus creates Xbox 360 controllers recognized by all games'
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
