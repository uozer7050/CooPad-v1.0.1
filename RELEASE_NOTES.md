# CooPad v5.1 - Release Notes

## 🔧 v1.0.1 - Build System Fix (February 2026)

### Windows Build Compatibility
- **Fixed**: Windows build now supports Python 3.12 and newer
- **Changed**: Migrated from `pygame` to `pygame-ce` (Community Edition)
  - pygame 2.6.1 fails on Python 3.12+ due to missing distutils module
  - pygame-ce is actively maintained and supports Python 3.12+
- **Improved**: Build scripts now validate they're run from repository root
- **Updated**: Documentation with Python 3.12+ requirements

**Breaking Change**: Users with Python 3.12+ must use pygame-ce instead of pygame
- `requirements.txt` now specifies `pygame-ce`
- Build scripts automatically install pygame-ce
- pygame-ce is a drop-in replacement with no code changes needed

---

## 🎉 Major Release: Ready for Public Open Source Distribution

CooPad v5.1 represents a major milestone with comprehensive improvements for public release as an open-source project. This release focuses on user experience, security, and ease of deployment.

## 🆕 What's New

### 1. Settings Tab with Configurable Update Rates
- **New Settings Tab**: Dedicated interface for network configuration
- **UDP Rate Selection**: Choose between 30Hz, 60Hz, or 90Hz
  - 30 Hz: Lower bandwidth, suitable for slower connections
  - 60 Hz: **Recommended** for most users (matches typical game frame rates)
  - 90 Hz: High performance for low-latency networks
- **Real-Time Adjustment**: Change rate on the fly without restarting

### 2. Network Telemetry Dashboard
- **Latency Monitoring**: Real-time packet latency in milliseconds
- **Jitter Measurement**: Network stability indicator
- **Packet Rate Display**: Actual packets per second
- **Sequence Tracking**: For packet loss detection
- Available in both Host and Client tabs

### 3. Enhanced Security
- **Packet Validation**: All incoming packets validated for size and content
- **Rate Limiting**: Protection against DoS attacks (150 packets/sec max per client)
- **Input Sanitization**: Gamepad values clamped to valid ranges
- **Protocol Versioning**: Ensures compatibility between client and host

### 4. Distribution-Ready Builds
- **Windows**: Single-file executable (coopad.exe)
  - No installation required
  - All dependencies bundled
  - Double-click to run
- **Linux**: Debian package (.deb)
  - Automatic dependency resolution
  - Desktop integration (start from menu)
  - Udev rules automatically configured
  - User automatically added to 'input' group

### 5. Improved Documentation
- **Comprehensive README**: Full English documentation
- **Turkish Changelog**: Detailed explanation of all changes (CHANGELOG_TR.md)
- **Removed Clutter**: Deleted obsolete technical documents
- **Clear Instructions**: Setup guides for both platforms

## 🔧 Technical Improvements

### Protocol Enhancements
- Added `validate_packet_size()` for size checking (max 1024 bytes)
- Added `validate_gamepad_state()` for input validation
- Version checking on all packets
- Better error handling and reporting

### Client Improvements
```python
# New configurable update rate
client = GamepadClient(update_rate=60)  # 30, 60, or 90 Hz

# Telemetry callback for real-time stats
client = GamepadClient(telemetry_cb=telemetry_handler)
```

### Host Improvements
```python
# Rate limiting per client
host._rate_limit_max = 150  # packets per second

# Telemetry tracking
host.telemetry_cb("Latency: 2.5ms | Jitter: 0.8ms")
```

### Backend API
```python
# Dynamic rate configuration
controller.set_update_rate(90)  # Change rate at runtime
```

## 📦 Building & Packaging

### Linux (.deb)
```bash
./scripts/build_deb.sh 1.0.0
# Creates: dist/coopad_1.0.0_amd64.deb
```

**Package includes:**
- Single-file executable with all dependencies
- Desktop entry for application menu
- Icon for system integration
- Udev rules for uinput access
- Post-install script for automatic setup

### Windows (.exe)
```batch
scripts\build_windows.bat 1.0.0
REM Creates: dist\coopad.exe
```

**or with PowerShell:**
```powershell
.\scripts\build_windows.ps1 1.0.0
```

### Cross-Platform
```bash
./scripts/build_all.sh 1.0.0
# Detects platform and builds accordingly
```

## 🔒 Security Features

### Protection Against Common Attacks

**1. Packet Flooding (DoS)**
- Rate limiting: Maximum 150 packets/second per client
- Per-client tracking with automatic blocking
- Logged but doesn't crash the host

**2. Malformed Packets**
- Size validation: 27-1024 bytes only
- Protocol version checking
- Field range validation (buttons, triggers, joysticks)

**3. Invalid Input Values**
- Buttons: 0-65535 (16 bits)
- Triggers: 0-255 (8 bits)
- Joysticks: -32768 to +32767 (16 bits signed)
- Sequence: 0-65535 (16 bits)

## 📊 Performance Metrics

### Network Performance by Update Rate

| Rate | Bandwidth | Latency | Use Case |
|------|-----------|---------|----------|
| 30 Hz | ~8 KB/s | +16ms | Slow networks, remote VPN |
| 60 Hz | ~16 KB/s | +8ms | **Recommended**, local LAN |
| 90 Hz | ~24 KB/s | +5ms | High-performance, low-latency |

### Tested Configurations
- ✅ Ubuntu 22.04 LTS (Host + Client)
- ✅ Ubuntu 24.04 LTS (Host + Client)
- ⏳ Windows 10 (Planned)
- ⏳ Windows 11 (Planned)

### Network Scenarios
- ✅ Same machine (localhost): <1ms latency
- ✅ Local LAN: 1-5ms latency
- ✅ VPN (Tailscale): 10-30ms latency

## 🎮 User Experience Improvements

### Before v5.1
```
❌ Manual dependency installation required
❌ No network statistics
❌ Fixed 60Hz rate
❌ Complex setup (run scripts, reboot)
❌ Unclear error messages
```

### After v5.1
```
✅ One-click installation (.deb or .exe)
✅ Real-time latency/jitter display
✅ Configurable 30/60/90 Hz rates
✅ Automatic setup (no user intervention)
✅ Clear, helpful error messages
```

## 🚀 Getting Started

### Linux Quick Start
```bash
# Download and install
wget https://github.com/uozer7050/v5.1/releases/download/v5.1/coopad_1.0.0_amd64.deb
sudo dpkg -i coopad_1.0.0_amd64.deb

# Run from menu or terminal
coopad
```

### Windows Quick Start
```
1. Download coopad.exe from Releases
2. (Optional) Install ViGEm Bus Driver for Host mode
3. Double-click coopad.exe
4. Done!
```

## 📝 Complete Feature List

### Core Functionality
- Remote gamepad over UDP network
- Full Xbox 360 controller emulation
- Cross-platform (Windows ↔ Linux)
- Low-latency packet transmission

### Network Features
- ✨ Configurable update rates (30/60/90 Hz)
- ✨ Real-time latency monitoring
- ✨ Jitter calculation and display
- ✨ Packet rate tracking
- ✨ Sequence number display

### Security Features
- ✨ Packet size validation
- ✨ Gamepad state validation
- ✨ Rate limiting (DoS protection)
- ✨ Protocol version checking

### UI Features
- ✨ Settings tab for configuration
- Host and Client tabs
- Platform status indicators
- Built-in help system
- Real-time telemetry display

### Distribution Features
- ✨ Windows single-file executable
- ✨ Linux .deb package
- ✨ Desktop integration (Linux)
- ✨ Automatic udev setup (Linux)
- Build scripts for both platforms

_(✨ = New in v5.1)_

## 🐛 Bug Fixes

- Fixed protocol import order issue
- Improved error handling in telemetry parsing
- Better handling of missing pygame on client
- More robust packet validation
- Fixed potential crash on malformed packets

## 🔮 Future Plans (v5.2+)

- [ ] Automatic network quality detection
- [ ] Adaptive rate adjustment
- [ ] Multiple controller support
- [ ] Recording/playback functionality
- [ ] Configuration profiles
- [ ] Windows MSI installer
- [ ] macOS support
- [ ] AppImage, Snap, and Flatpak packages

## 📞 Support & Contributing

### Report Issues
- GitHub Issues: https://github.com/uozer7050/v5.1/issues

### Contribute
- Pull Requests welcome!
- See README.md for development setup

### Community
- GitHub Discussions for questions and feedback

## 📄 License

Open Source - See LICENSE file for details

## 🙏 Acknowledgments

This release is dedicated to the gaming community. Thank you for your support!

---

**Download CooPad v5.1:**
- Linux: `coopad_1.0.0_amd64.deb`
- Windows: `coopad.exe`

**Links:**
- Repository: https://github.com/uozer7050/v5.1
- Documentation: README.md
- Changelog (Turkish): CHANGELOG_TR.md

**Release Date:** February 2026  
**Version:** 5.1.0
