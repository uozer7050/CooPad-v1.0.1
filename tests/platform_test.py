#!/usr/bin/env python3
"""
Cross-platform compatibility test for CooPad
Tests host and client functionality on Linux and Windows
"""
import os
import sys
import platform
import time
import threading
from typing import Dict, List, Tuple


class PlatformChecker:
    """Check platform-specific requirements and compatibility"""
    
    def __init__(self):
        self.os_name = platform.system()
        self.python_version = sys.version
        self.arch = platform.machine()
        self.issues: List[Tuple[str, str, str]] = []  # (severity, component, message)
        
    def check_all(self) -> Dict:
        """Run all compatibility checks"""
        print(f"=== CooPad Cross-Platform Compatibility Test ===")
        print(f"Platform: {self.os_name}")
        print(f"Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        print(f"Architecture: {self.arch}\n")
        
        results = {
            'platform': self.os_name,
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}",
            'checks': {}
        }
        
        # Core dependencies
        results['checks']['tkinter'] = self._check_tkinter()
        results['checks']['pillow'] = self._check_pillow()
        results['checks']['pygame'] = self._check_pygame()
        
        # Platform-specific dependencies
        if self.os_name == 'Linux':
            results['checks']['evdev'] = self._check_evdev()
            results['checks']['uinput'] = self._check_uinput()
        elif self.os_name == 'Windows':
            results['checks']['vgamepad'] = self._check_vgamepad()
        
        # Network functionality
        results['checks']['network'] = self._check_network()
        
        # Host/Client functionality
        results['checks']['host'] = self._check_host_functionality()
        results['checks']['client'] = self._check_client_functionality()
        
        return results
    
    def _check_tkinter(self) -> Dict:
        """Check if tkinter is available for GUI"""
        try:
            import tkinter
            print("✓ tkinter: Available")
            return {'status': 'ok', 'message': 'Available'}
        except ImportError as e:
            msg = f"Not available. Install with: sudo apt-get install python3-tk (Linux) or reinstall Python with tk support (Windows)"
            print(f"✗ tkinter: {msg}")
            self.issues.append(('ERROR', 'GUI', msg))
            return {'status': 'error', 'message': str(e)}
    
    def _check_pillow(self) -> Dict:
        """Check if Pillow is available for image handling"""
        try:
            import PIL
            print(f"✓ Pillow: Available (version {PIL.__version__})")
            return {'status': 'ok', 'message': f'Version {PIL.__version__}'}
        except ImportError as e:
            msg = "Not available. Install with: pip install Pillow"
            print(f"✗ Pillow: {msg}")
            self.issues.append(('ERROR', 'GUI', msg))
            return {'status': 'error', 'message': str(e)}
    
    def _check_pygame(self) -> Dict:
        """Check if pygame is available for joystick input"""
        try:
            import pygame
            print(f"✓ pygame: Available")
            return {'status': 'ok', 'message': 'Available for joystick input'}
        except ImportError as e:
            msg = "Not available. Install with: pip install pygame"
            print(f"✗ pygame: {msg}")
            self.issues.append(('WARNING', 'Client', 'Joystick input will not be available'))
            return {'status': 'warning', 'message': str(e)}
    
    def _check_evdev(self) -> Dict:
        """Check if evdev is available (Linux only)"""
        try:
            import evdev
            print(f"✓ evdev: Available (Linux virtual gamepad support)")
            return {'status': 'ok', 'message': 'Virtual gamepad support available'}
        except ImportError as e:
            msg = "Not available. Install with: pip install evdev"
            print(f"✗ evdev: {msg}")
            self.issues.append(('ERROR', 'Host', 'Virtual gamepad creation will fail'))
            return {'status': 'error', 'message': str(e)}
    
    def _check_uinput(self) -> Dict:
        """Check if uinput device is accessible (Linux only)"""
        try:
            if not os.path.exists('/dev/uinput'):
                msg = "/dev/uinput device not found. Load uinput module with: sudo modprobe uinput"
                print(f"✗ uinput device: {msg}")
                self.issues.append(('ERROR', 'Host', msg))
                return {'status': 'error', 'message': msg}
            
            # Check permissions
            import stat
            st = os.stat('/dev/uinput')
            mode = st.st_mode
            
            # Check if we can access it
            if os.access('/dev/uinput', os.W_OK):
                print("✓ uinput device: Accessible")
                return {'status': 'ok', 'message': 'Device accessible'}
            else:
                msg = "Device exists but not accessible. Run scripts/setup_uinput.sh or run as root"
                print(f"⚠ uinput device: {msg}")
                self.issues.append(('WARNING', 'Host', msg))
                return {'status': 'warning', 'message': msg}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _check_vgamepad(self) -> Dict:
        """Check if vgamepad is available (Windows only)"""
        try:
            import vgamepad
            print("✓ vgamepad: Available (Windows ViGEm virtual gamepad support)")
            return {'status': 'ok', 'message': 'ViGEm virtual gamepad support available'}
        except ImportError as e:
            msg = "Not available. Install ViGEm Bus Driver and: pip install vgamepad"
            print(f"✗ vgamepad: {msg}")
            self.issues.append(('ERROR', 'Host', 'Virtual gamepad creation will fail on Windows'))
            return {'status': 'error', 'message': str(e)}
    
    def _check_network(self) -> Dict:
        """Check network functionality"""
        try:
            import socket
            # Try to create a UDP socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.close()
            print("✓ Network: UDP sockets available")
            return {'status': 'ok', 'message': 'UDP sockets work'}
        except Exception as e:
            msg = f"Network error: {e}"
            print(f"✗ Network: {msg}")
            self.issues.append(('ERROR', 'Network', msg))
            return {'status': 'error', 'message': str(e)}
    
    def _check_host_functionality(self) -> Dict:
        """Test host can start and bind to port"""
        try:
            from gp.core.host import GamepadHost
            
            # Create a test host
            msgs = []
            def capture(msg):
                msgs.append(msg)
            
            host = GamepadHost(bind_ip='127.0.0.1', port=17777, status_cb=capture)
            host.start()
            time.sleep(0.5)
            host.stop()
            time.sleep(0.3)
            
            # Check if it started successfully
            if any('listening' in m.lower() for m in msgs):
                print("✓ Host: Can start and bind to port")
                return {'status': 'ok', 'message': 'Host functional'}
            else:
                msg = "Host started but no listening message"
                print(f"⚠ Host: {msg}")
                return {'status': 'warning', 'message': msg}
        except Exception as e:
            msg = f"Host start failed: {e}"
            print(f"✗ Host: {msg}")
            self.issues.append(('ERROR', 'Host', msg))
            return {'status': 'error', 'message': str(e)}
    
    def _check_client_functionality(self) -> Dict:
        """Test client can send packets"""
        try:
            from gp.core.client import GamepadClient
            
            # Create a test client
            msgs = []
            def capture(msg):
                msgs.append(msg)
            
            client = GamepadClient(target_ip='127.0.0.1', port=17778, status_cb=capture)
            client.start()
            time.sleep(0.3)
            client.stop()
            time.sleep(0.2)
            
            # Check if it started successfully
            if any('sending' in m.lower() for m in msgs):
                print("✓ Client: Can send packets")
                return {'status': 'ok', 'message': 'Client functional'}
            else:
                msg = "Client started but no sending message"
                print(f"⚠ Client: {msg}")
                return {'status': 'warning', 'message': msg}
        except Exception as e:
            msg = f"Client start failed: {e}"
            print(f"✗ Client: {msg}")
            self.issues.append(('ERROR', 'Client', msg))
            return {'status': 'error', 'message': str(e)}
    
    def print_summary(self):
        """Print summary of issues"""
        print("\n=== Summary ===")
        
        if not self.issues:
            print("✓ All checks passed! CooPad should work on this platform.")
            return
        
        errors = [i for i in self.issues if i[0] == 'ERROR']
        warnings = [i for i in self.issues if i[0] == 'WARNING']
        
        if errors:
            print(f"\n❌ {len(errors)} ERROR(S) found:")
            for severity, component, msg in errors:
                print(f"   [{component}] {msg}")
        
        if warnings:
            print(f"\n⚠️  {len(warnings)} WARNING(S) found:")
            for severity, component, msg in warnings:
                print(f"   [{component}] {msg}")
        
        # Platform-specific advice
        print("\n=== Platform-Specific Advice ===")
        if self.os_name == 'Linux':
            print("For Linux Host:")
            print("  - Ensure uinput module is loaded: sudo modprobe uinput")
            print("  - Run scripts/setup_uinput.sh to configure permissions")
            print("  - Or run the host with: sudo -E python3 main.py")
            print("\nFor Linux Client:")
            print("  - Install pygame: pip install pygame")
            print("  - Connect a USB gamepad or use virtual joystick")
        elif self.os_name == 'Windows':
            print("For Windows Host:")
            print("  - Install ViGEm Bus Driver from: https://github.com/ViGEm/ViGEmBus/releases")
            print("  - Install vgamepad: pip install vgamepad")
            print("\nFor Windows Client:")
            print("  - Install pygame: pip install pygame")
            print("  - Windows may require additional firewall rules for UDP traffic")


def main():
    """Run platform compatibility check"""
    checker = PlatformChecker()
    results = checker.check_all()
    checker.print_summary()
    
    # Return exit code based on errors
    has_errors = any(v.get('status') == 'error' for v in results['checks'].values())
    sys.exit(1 if has_errors else 0)


if __name__ == '__main__':
    main()
