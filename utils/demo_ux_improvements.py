#!/usr/bin/env python3
"""
Demonstration of improved user experience features
Shows platform detection and user-friendly error messages
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from platform_info import get_platform_info


def print_box(title, lines, color=''):
    """Print a colored box with content."""
    colors = {
        'green': '\033[92m',
        'yellow': '\033[93m',
        'red': '\033[91m',
        'blue': '\033[94m',
        'reset': '\033[0m',
        'bold': '\033[1m'
    }
    
    c = colors.get(color, '')
    reset = colors['reset'] if color else ''
    bold = colors['bold']
    
    width = max(len(line) for line in lines) + 4
    print(f"\n{c}{'═' * width}{reset}")
    print(f"{c}║ {bold}{title}{reset}{c}{' ' * (width - len(title) - 3)}║{reset}")
    print(f"{c}{'═' * width}{reset}")
    for line in lines:
        padding = width - len(line) - 4
        print(f"{c}║{reset} {line}{' ' * padding} {c}║{reset}")
    print(f"{c}{'═' * width}{reset}")


def demonstrate_platform_detection():
    """Demonstrate the platform detection feature."""
    print("\n" + "="*70)
    print("CooPad - Improved User Experience Demo")
    print("="*70)
    
    pinfo = get_platform_info()
    
    # Platform info
    print_box(
        f"Detected Platform: {pinfo.get_platform_name()}",
        [
            f"System: {pinfo.os_name}",
            f"Windows: {'Yes' if pinfo.is_windows else 'No'}",
            f"Linux: {'Yes' if pinfo.is_linux else 'No'}"
        ],
        'blue'
    )
    
    # Host status
    host_status = pinfo.get_host_status()
    color_map = {'ready': 'green', 'warning': 'yellow', 'error': 'red'}
    
    lines = [
        f"Status: {host_status['status'].upper()}",
        f"Icon: {host_status['icon']}",
        f"Message: {host_status['message']}",
        f"Details: {host_status.get('details', 'N/A')}"
    ]
    if 'action' in host_status:
        lines.append(f"Action: {host_status['action']}")
    
    print_box(
        "HOST MODE - Virtual Gamepad",
        lines,
        color_map.get(host_status['status'], '')
    )
    
    # Client status
    client_status = pinfo.get_client_status()
    
    lines = [
        f"Status: {client_status['status'].upper()}",
        f"Icon: {client_status['icon']}",
        f"Message: {client_status['message']}",
        f"Details: {client_status.get('details', 'N/A')}"
    ]
    if 'action' in client_status:
        lines.append(f"Action: {client_status['action']}")
    
    print_box(
        "CLIENT MODE - Gamepad Input",
        lines,
        color_map.get(client_status['status'], '')
    )
    
    # Compatibility info
    compat = pinfo.get_compatibility_info()
    
    lines = [
        f"Can act as Host: {'✓ YES' if compat['can_host'] else '✗ NO'}",
        f"Can act as Client: {'✓ YES' if compat['can_client'] else '✗ NO'}",
        "",
        "Cross-Platform Compatibility:"
    ] + [f"  • {note}" for note in compat.get('notes', [])]
    
    print_box(
        "COMPATIBILITY STATUS",
        lines,
        'blue'
    )
    
    # Setup instructions
    setup = pinfo.get_setup_instructions()
    
    print_box(
        "SETUP INSTRUCTIONS - HOST MODE",
        setup['host'],
        'yellow'
    )
    
    print_box(
        "SETUP INSTRUCTIONS - CLIENT MODE",
        setup['client'],
        'yellow'
    )
    
    # Example error messages
    print("\n" + "="*70)
    print("EXAMPLE ERROR MESSAGES (User-Friendly)")
    print("="*70)
    
    if host_status['status'] == 'error':
        print_box(
            "⚠ HOST START FAILED",
            [
                f"✗ Cannot start: {host_status['message']}",
                f"→ Solution: {host_status.get('action', host_status.get('details', ''))}"
            ],
            'red'
        )
    elif host_status['status'] == 'warning':
        print_box(
            "⚠ HOST WARNING",
            [
                f"⚠ Warning: {host_status['message']}",
                f"→ {host_status.get('details', '')}",
                "Host can still start but may need sudo/permissions"
            ],
            'yellow'
        )
    else:
        print_box(
            "✓ HOST READY",
            [
                f"✓ {host_status['message']}",
                "Host is ready to receive gamepad input from clients"
            ],
            'green'
        )
    
    # Cross-platform explanation
    print("\n" + "="*70)
    print("CROSS-PLATFORM GAMEPAD INPUT TRANSMISSION")
    print("="*70)
    
    explanation = [
        "",
        "HOW IT WORKS:",
        "  1. Client captures physical gamepad input (buttons, sticks, triggers)",
        "  2. Input is encoded into binary packets (UDP protocol)",
        "  3. Packets are sent over network to Host IP:Port",
        "  4. Host receives and decodes packets",
        "  5. Host creates virtual gamepad with received input",
        "  6. Games see virtual gamepad as real hardware",
        "",
        "PLATFORM COMPATIBILITY:",
        "  ✓ Linux Client → Windows Host (YES - packets are platform-agnostic)",
        "  ✓ Windows Client → Linux Host (YES - packets are platform-agnostic)",
        "  ✓ Linux Client → Linux Host (YES - same platform)",
        "  ✓ Windows Client → Windows Host (YES - same platform)",
        "",
        "VIRTUAL GAMEPAD DRIVERS:",
        "  • Windows Host: Uses ViGEmBus to create Xbox 360 controller",
        "  • Linux Host: Uses evdev/uinput to create standard joystick",
        "  • Both appear as real hardware to games",
        "",
        "PACKET FORMAT:",
        "  • Binary protocol (protocol version 2)",
        "  • Contains: buttons (16-bit), triggers (8-bit each), sticks (16-bit each)",
        "  • Platform-independent: works regardless of client/host OS",
        "  • Network order: ensures cross-platform compatibility",
        ""
    ]
    
    for line in explanation:
        print(line)
    
    print("="*70)


if __name__ == '__main__':
    demonstrate_platform_detection()
