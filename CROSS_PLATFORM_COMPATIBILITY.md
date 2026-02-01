# CooPad Cross-Platform Compatibility Guide

## Overview

CooPad is a remote gamepad application that allows a client to send gamepad inputs over the network to a host, which creates a virtual gamepad. This document describes the cross-platform compatibility status and requirements for both Linux and Windows.

## Test Results Summary

✅ **CooPad works on both Linux and Windows as host and client**

The application has been tested and confirmed to work in the following configurations:
- ✅ Linux Host + Linux Client
- ✅ Linux Host + Windows Client (cross-platform)
- ✅ Windows Host + Linux Client (cross-platform)
- ✅ Windows Host + Windows Client

## Platform-Specific Requirements

### Linux

#### System Requirements
- Ubuntu 20.04+ or equivalent Linux distribution
- Python 3.8+ (tested with Python 3.12.3)
- X11 or Wayland display server (for GUI)

#### Required System Packages
```bash
sudo apt-get update
sudo apt-get install python3-tk python3-dev build-essential
```

#### Python Dependencies
```bash
pip install Pillow pygame evdev
```

#### Host-Specific Setup (Virtual Gamepad)

Linux hosts use **evdev/uinput** to create virtual gamepad devices. This requires:

1. **Load uinput kernel module:**
```bash
sudo modprobe uinput
# Make it persistent across reboots:
echo "uinput" | sudo tee -a /etc/modules
```

2. **Configure permissions (recommended):**
```bash
# Run the provided setup script
chmod +x scripts/setup_uinput.sh
./scripts/setup_uinput.sh
# Then log out and log back in, or run: newgrp input
```

3. **Alternative - Run as root (for testing):**
```bash
sudo -E python3 main.py
```

#### Client-Specific Setup (Joystick Input)

- Install pygame: `pip install pygame`
- Connect USB gamepad or use virtual joystick
- No special permissions required for client

### Windows

#### System Requirements
- Windows 10/11 (64-bit recommended)
- Python 3.8+ for Windows
- Admin rights for initial driver installation

#### Python Dependencies
```bash
pip install Pillow pygame vgamepad
```

#### Host-Specific Setup (Virtual Gamepad)

Windows hosts use **ViGEm Bus Driver** to create virtual Xbox 360 gamepads:

1. **Install ViGEm Bus Driver:**
   - Download from: https://github.com/ViGEm/ViGEmBus/releases
   - Run installer with administrator privileges
   - Reboot if prompted

2. **Install vgamepad:**
```bash
pip install vgamepad
```

#### Client-Specific Setup

- Install pygame: `pip install pygame`
- Windows may prompt for firewall rules when running the client
- Allow Python through Windows Firewall for private networks

#### Firewall Configuration

If connection fails, manually configure Windows Firewall:

1. Open Windows Defender Firewall
2. Click "Allow an app through firewall"
3. Add Python (python.exe) if not listed
4. Enable for "Private" networks
5. Alternatively, create an inbound rule for UDP port 7777

## Cross-Platform Communication

### Network Requirements

Both host and client **must be on the same local network**, or connected via a virtual private network (VPN).

**Recommended VPN solutions for remote play:**
- ZeroTier (https://www.zerotier.com/)
- Tailscale (https://tailscale.com/)
- Hamachi
- Wireguard

### Protocol

- **Protocol:** UDP
- **Default Port:** 7777
- **Packet Format:** Binary (see gp/core/protocol.py)
- **Latency:** Typically 1-10ms on local network

### Supported Gamepad Features

| Feature | Linux Host | Windows Host | Notes |
|---------|-----------|--------------|-------|
| D-Pad | ✅ | ✅ | 4-way directional |
| Face Buttons (A/B/X/Y) | ✅ | ✅ | Full support |
| Shoulder Buttons (LB/RB) | ✅ | ✅ | Full support |
| Triggers (LT/RT) | ✅ | ✅ | 0-255 range |
| Left Stick | ✅ | ✅ | -32768 to 32767 |
| Right Stick | ✅ | ✅ | -32768 to 32767 |
| Thumbstick Clicks | ✅ | ✅ | L3/R3 buttons |
| Start/Select | ✅ | ✅ | Full support |

## Known Issues and Limitations

### Linux Host Issues

1. **Permission Denied on /dev/uinput**
   - **Symptom:** Host fails to create virtual gamepad
   - **Solution:** Run `scripts/setup_uinput.sh` or use `sudo -E python3 main.py`

2. **ALSA Audio Warnings**
   - **Symptom:** "ALSA lib" warnings in console
   - **Impact:** Cosmetic only, does not affect functionality
   - **Solution:** Can be ignored in headless environments

3. **D-Pad Mapping**
   - **Symptom:** D-pad may not work perfectly in some games
   - **Cause:** Linux uses hat axis for D-pad, some games expect buttons
   - **Workaround:** Use gamepad mapper utilities if needed

### Windows Host Issues

1. **ViGEm Driver Not Installed**
   - **Symptom:** "vgamepad init error" in logs
   - **Solution:** Install ViGEm Bus Driver from GitHub releases

2. **Antivirus/Firewall Blocking**
   - **Symptom:** Client cannot connect to host
   - **Solution:** Add exception for Python or the application

3. **Admin Rights Required**
   - **Symptom:** First run may fail
   - **Solution:** ViGEm requires admin rights for driver installation only

### Client Issues (Both Platforms)

1. **No Joystick Detected**
   - **Symptom:** Client sends only heartbeats
   - **Behavior:** This is expected; client will work but send neutral inputs
   - **Solution:** Connect a USB gamepad or use virtual joystick software

2. **Pygame Audio Warnings**
   - **Symptom:** SDL/pygame audio errors
   - **Impact:** Cosmetic only, does not affect functionality
   - **Solution:** Can be ignored

### Network Issues

1. **Different Networks**
   - **Symptom:** Client cannot reach host
   - **Solution:** Use VPN to connect networks (ZeroTier, Tailscale)

2. **Firewall Blocking UDP**
   - **Symptom:** No communication between client and host
   - **Solution:** Allow UDP port 7777 in firewall

## Testing Your Setup

### Quick Test

1. **Run the platform compatibility checker:**
```bash
python3 platform_test.py
```

This will check all dependencies and test basic functionality.

### Integration Test

2. **Run the full integration test:**
```bash
python3 integration_test.py
```

This starts both host and client locally and verifies communication.

### GUI Test

3. **Start the GUI application:**

Linux:
```bash
python3 main.py
```

Windows:
```bash
python main.py
```

## Performance Expectations

### Local Network (Ethernet)
- Latency: 1-3ms
- No packet loss
- Suitable for fast-paced games

### Local Network (WiFi)
- Latency: 3-10ms
- Occasional packet loss possible
- Suitable for most games

### VPN/Remote
- Latency: 20-100ms depending on distance
- May experience packet loss
- Best for turn-based or slower games

## Troubleshooting

### Linux Host Won't Start

```bash
# Check if uinput module is loaded
lsmod | grep uinput

# Load it if missing
sudo modprobe uinput

# Check device permissions
ls -l /dev/uinput

# Test with sudo
sudo -E python3 main.py
```

### Windows Host Won't Start

```powershell
# Check if ViGEm is installed
sc query ViGEmBus

# Reinstall ViGEm if needed
# Download from https://github.com/ViGEm/ViGEmBus/releases
```

### Client Can't Connect

```bash
# Test network connectivity
ping <host_ip>

# Check if port is open (on host)
sudo netstat -tulpn | grep 7777  # Linux
netstat -an | findstr 7777        # Windows

# Test with localhost first
# Set IP to 127.0.0.1 in client
```

## Development and Debugging

### Enable Debug Logging

Edit `main.py` and set logging level to DEBUG:

```python
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(message)s')
```

### Check Logs

Integration test logs are saved in `logs/` directory:
- `logs/host.log` - Host activity
- `logs/client.log` - Client activity

### Common Error Messages

| Error | Component | Meaning | Solution |
|-------|-----------|---------|----------|
| `vgamepad init error` | Host (Windows) | ViGEm driver not installed | Install ViGEm Bus Driver |
| `uinput init error` | Host (Linux) | Can't access /dev/uinput | Run setup script or use sudo |
| `bad version X from Y` | Host | Protocol mismatch | Update both host and client |
| `recv error: Bad file descriptor` | Host | Socket closed (normal on shutdown) | Ignore, this is expected |
| `no joystick found` | Client | No gamepad connected | Connect gamepad or ignore |

## Contributing

When testing new platforms or configurations:

1. Run `python3 platform_test.py` and report results
2. Document any new issues in GitHub issues
3. Submit PRs for fixes or improvements

## Support

For issues or questions:
- Check this compatibility guide first
- Review existing GitHub issues
- Create a new issue with platform details and error logs

## Version History

- v1.0: Initial cross-platform support
- Linux: evdev/uinput virtual gamepad
- Windows: ViGEm/vgamepad virtual gamepad
- Protocol version: 2
