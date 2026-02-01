# CooPad — Remote Gamepad

CooPad is a cross-platform remote gamepad application that allows you to use a gamepad over the network. A client captures gamepad inputs and sends them to a host, which creates a virtual gamepad that games can use.

## 🎯 New: Enhanced User Experience

**Version 5.1 includes major UX improvements:**
- 🟢 **Smart Platform Detection**: Automatically detects your OS and available drivers
- 💡 **User-Friendly Error Messages**: Clear explanations with actionable solutions
- 📊 **Visual Status Indicators**: Color-coded status (✓/⚠/✗) for instant feedback
- 📚 **Built-in Help System**: Platform-specific setup guides and troubleshooting
- 🔍 **Pre-Flight Checks**: Validates capabilities before starting to prevent errors

**See [UX_IMPROVEMENTS_TR.md](UX_IMPROVEMENTS_TR.md) for details (Turkish) or [CROSS_PLATFORM_TECHNICAL_EXPLANATION.md](CROSS_PLATFORM_TECHNICAL_EXPLANATION.md) for technical details.**

## ✅ Cross-Platform Support

CooPad works on both **Linux** and **Windows** as host and client:
- ✅ Linux Host + Linux Client
- ✅ Linux Host + Windows Client
- ✅ Windows Host + Linux Client  
- ✅ Windows Host + Windows Client

**📖 See [CROSS_PLATFORM_COMPATIBILITY.md](CROSS_PLATFORM_COMPATIBILITY.md) for detailed setup instructions, troubleshooting, and known issues.**

## Quick Start

### Test Your Platform

Run the compatibility checker to verify your setup:
```bash
python3 platform_test.py
```

### Installation

#### Linux
```bash
# Install system packages
sudo apt update
sudo apt install python3-tk python3-dev build-essential

# Install Python packages
pip install -r requirements.txt

# Setup uinput permissions (for host)
chmod +x scripts/setup_uinput.sh
./scripts/setup_uinput.sh
# Then log out and back in
```

#### Windows
```bash
# Install ViGEm Bus Driver (for host)
# Download from: https://github.com/ViGEm/ViGEmBus/releases

# Install Python packages
pip install -r requirements.txt
pip install vgamepad
```

### Run the Application

```bash
# Start the GUI
python3 main.py  # Linux
python main.py   # Windows
```

## Testing

```bash
# Platform compatibility check
python3 platform_test.py

# Full integration test (host + client)
python3 integration_test.py

# Cross-platform compatibility tests
python3 test_cross_platform.py

# UX improvements demonstration
python3 demo_ux_improvements.py

# UI mockup visualization
python3 ui_mockup.py
```

## Documentation

### User Experience & Setup
- **[UX_IMPROVEMENTS_TR.md](UX_IMPROVEMENTS_TR.md)** - Turkish documentation of UI improvements
  - All user questions answered
  - Error message improvements
  - Platform status indicators
  - Cross-platform explanation

- **[CROSS_PLATFORM_TECHNICAL_EXPLANATION.md](CROSS_PLATFORM_TECHNICAL_EXPLANATION.md)** - Technical deep-dive
  - Why cross-platform works
  - Packet format explanation
  - Platform independence proof
  - Virtual gamepad creation details

### Complete Guides
- **[CROSS_PLATFORM_COMPATIBILITY.md](CROSS_PLATFORM_COMPATIBILITY.md)** - Complete cross-platform guide
  - Platform-specific requirements
  - Setup instructions for Linux and Windows
  - Known issues and troubleshooting
  - Performance expectations
  - Network configuration

- **[TEST_SONUCLARI_TR.md](TEST_SONUCLARI_TR.md)** - Turkish test results
- **[TESTING_SUMMARY.md](TESTING_SUMMARY.md)** - Executive summary

## Features

- Remote gamepad over local network or VPN
- Full Xbox 360 gamepad emulation
- Low latency (1-10ms on local network)
- Cross-platform: Linux ↔ Windows
- No special drivers needed on client
- Supports physical gamepad input via pygame

## Requirements

### Common (Both Platforms)
- Python 3.8+
- Pillow
- pygame

### Linux Host
- evdev (virtual gamepad via uinput)
- uinput kernel module
- Permissions for /dev/uinput

### Windows Host
- vgamepad (virtual gamepad via ViGEm)
- ViGEm Bus Driver

### Client (Both Platforms)
- pygame (for joystick input)
- Network access to host

## License

See LICENSE file for details.