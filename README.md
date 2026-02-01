# CooPad — Remote Gamepad over Network

**Cross-platform remote gamepad application for gaming over network**

CooPad allows you to use a physical gamepad connected to one computer (Client) to control games on another computer (Host) over a local network or VPN. Perfect for couch gaming, game streaming, or playing with friends remotely.

## 🎮 Features

- **Cross-Platform Support**: Works on Windows and Linux (all combinations supported)
- **Controller Profiles**: Built-in support for PS4, PS5, Xbox 360, and generic controllers
- **Low Latency**: 1-10ms on local networks, optimized for real-time gaming
- **Configurable Update Rates**: Choose between 30Hz, 60Hz, or 90Hz for optimal performance
- **Real-Time Telemetry**: Monitor latency, jitter, and packet rates
- **Smart Platform Detection**: Automatically detects your OS and available drivers
- **User-Friendly Interface**: Clean GUI with helpful status indicators and setup guides
- **Secure**: Built-in packet validation and rate limiting protection

## 🚀 Quick Start

### Installation

#### Windows

**Option 1: Download executable (Recommended)**
```
1. Download coopad.exe from Releases
2. Double-click to run
3. (Optional) Create a shortcut on your desktop
```

**Option 2: Run from source**
```bash
# Install Python dependencies
pip install -r requirements.txt

# For Host mode, install ViGEm Bus Driver:
# Download from: https://github.com/ViGEm/ViGEmBus/releases

# Run the application
python main.py
```

#### Linux

**Option 1: Install .deb package (Recommended)**
```bash
# Download the latest .deb from Releases
sudo dpkg -i coopad_*.deb

# The package automatically installs dependencies
# Run from applications menu or terminal
coopad
```

**Option 2: Run from source**
```bash
# Install system dependencies
sudo apt update
sudo apt install python3-tk python3-dev python3-pip

# Install Python dependencies
pip3 install -r requirements.txt

# Run the application
python3 main.py
```

### Basic Usage

1. **Start Host** (on the computer where you want to play games):
   - Open CooPad
   - Click "Start Host" 
   - Games will now see a virtual Xbox 360 controller

2. **Start Client** (on the computer with the physical gamepad):
   - Open CooPad
   - Enter the Host's IP address
   - Click "Start Client"
   - Your gamepad inputs will be sent to the Host

3. **Configure Settings**:
   - Go to the Settings tab
   - Choose your controller type:
     - PS4 Controller
     - PS5 Controller
     - Xbox 360 Controller
     - Generic (for other controllers)
   - Choose update rate based on your network:
     - 30 Hz: Lower bandwidth, suitable for slower networks
     - 60 Hz: Recommended for most users
     - 90 Hz: High performance for low-latency networks

## 📡 Network Setup

### Local Network (Same WiFi/LAN)
- Both computers must be on the same network
- Default port: 7777 (UDP)
- Firewall may need to allow the application

### Remote/Internet (VPN Required)
For playing over the internet, use a VPN solution:
- **ZeroTier**: Easy setup, free tier available
- **Tailscale**: Modern, automatic, free for personal use
- **Hamachi**: Classic VPN solution
- **WireGuard**: Advanced users, self-hosted

## 🖥️ Platform-Specific Setup

### Windows Host Requirements
- **ViGEm Bus Driver**: Virtual gamepad driver
  - Download from: https://github.com/ViGEm/ViGEmBus/releases
  - Install the driver before running CooPad
  - Requires administrator privileges to install

### Linux Host Requirements
- **evdev**: For virtual gamepad creation (automatically installed by .deb package)
- **uinput module**: Must be loaded and accessible

The .deb package automatically:
- Installs evdev library and dependencies
- Installs udev rules for uinput access
- Adds user to 'input' group
- Loads the uinput module

**Manual setup (if running from source):**
```bash
# Install evdev
pip3 install evdev

# Load uinput module
sudo modprobe uinput

# Setup permissions
./scripts/setup_uinput.sh

# Then log out and back in
```

### Client Requirements (Both Platforms)
- **pygame-ce**: For reading physical gamepad input (pygame-ce 2.4+ required for Python 3.12+)
- **Physical gamepad**: USB or Bluetooth connected (PS4, PS5, Xbox 360, or generic)
- Client can run without a physical gamepad (sends test data)

**Note**: If you have Python 3.12 or newer, pygame-ce (Community Edition) is required instead of the legacy pygame package.

## 🎮 Controller Support

CooPad includes built-in profiles for popular controllers:
- **PlayStation 4 Controller**: Proper axis and button mapping for DS4
- **PlayStation 5 Controller**: DualSense support with hat-based D-pad
- **Xbox 360 Controller**: Correct mapping including combined trigger axis
- **Generic Controller**: Fallback for other standard controllers

See [Controller Profiles Guide](docs/CONTROLLER_PROFILES.md) for detailed mapping information.

## 📊 Monitoring & Performance

### Network Statistics
Both Host and Client tabs show real-time telemetry:
- **Latency**: Round-trip time for packets (lower is better)
- **Jitter**: Variation in latency (lower is better)
- **Packet Rate**: Actual packets per second
- **Sequence Number**: For packet loss detection

### Optimal Settings
- **LAN**: 60-90 Hz for smooth gameplay
- **VPN (Same City)**: 60 Hz recommended
- **VPN (Remote)**: 30-60 Hz depending on connection quality
- **WiFi**: Start with 60 Hz, adjust based on performance

## 🔒 Security Features

- **Packet Validation**: All packets are validated for size and content
- **Rate Limiting**: Protection against DoS attacks (150 packets/sec max)
- **Input Sanitization**: Gamepad values are clamped to valid ranges
- **Version Checking**: Ensures protocol compatibility

## 🛠️ Building from Source

### Build Requirements
- Python 3.8+ (Python 3.12+ recommended)
- PyInstaller
- Platform-specific requirements (see above)

**Important for Python 3.12+**: The build scripts automatically use `pygame-ce` (Community Edition) which supports Python 3.12 and newer. The legacy `pygame` package does not support Python 3.12+.

**Windows Build Note**: The build process uses a custom PyInstaller spec file (`coopad.spec`) that ensures the ViGEmClient.dll files from the vgamepad package are properly bundled. If you encounter DLL loading errors, ensure that:
1. vgamepad is installed: `pip install vgamepad`
2. The spec file is used: `pyinstaller coopad.spec`
3. The `hook-vgamepad.py` file is present in the project root

### Build Commands

**Windows executable:**
```bash
# Must be run from the repository root directory
scripts\build_windows.bat 1.0.0
# or
.\scripts\build_windows.ps1 1.0.0
```

**Linux .deb package:**
```bash
./scripts/build_deb.sh 1.0.0
```

**Both platforms:**
```bash
./scripts/build_all.sh 1.0.0
```

Output will be in the `dist/` directory.

## 🐛 Troubleshooting

### Host Won't Start
**Windows:**
- Install ViGEm Bus Driver from official releases
- Restart computer after driver installation
- Run as Administrator if needed

**Linux:**
- If using .deb package: Dependencies are installed automatically
- Check if uinput module is loaded: `lsmod | grep uinput`
- Check permissions: `ls -l /dev/uinput`
- Run setup script: `./scripts/setup_uinput.sh`
- Or run with sudo: `sudo -E python3 main.py`

### Client Can't Connect
- Verify both devices are on the same network
- Check firewall settings (allow UDP port 7777)
- Test with localhost first: use 127.0.0.1 as target
- For VPN: ensure both devices are connected to VPN

### High Latency/Jitter
- Switch to a wired connection instead of WiFi
- Lower the update rate (Settings tab)
- Close bandwidth-intensive applications
- Check for network congestion

### No Gamepad Detected (Client)
- Ensure gamepad is connected and working
- Install pygame-ce: `pip install pygame-ce` (for Python 3.12+)
- Or install pygame: `pip install pygame` (for Python 3.11 and earlier)
- Test gamepad with system tools first
- Client can run without gamepad (sends test data)

## 📝 Technical Details

### Protocol
- **Transport**: UDP for low latency
- **Port**: 7777 (configurable)
- **Packet Format**: Binary struct (27 bytes)
- **Version**: Protocol v2

### Supported Platforms
- ✅ Linux (Host + Client)
- ✅ Windows (Host + Client)
- ✅ All cross-platform combinations work

### Virtual Gamepad
- **Linux**: evdev/uinput driver
- **Windows**: ViGEm Bus Driver (Xbox 360 emulation)
- **Format**: Full Xbox 360 controller layout

## 📁 Project Structure

```
v5.1/
├── gp/                    # Core gamepad communication package
│   └── core/             # Host and client implementations
│       ├── client.py     # Client-side gamepad capture
│       ├── host.py       # Host-side virtual gamepad
│       └── protocol.py   # Network protocol definitions
├── docs/                  # Documentation
│   ├── PYINSTALLER_FIX.md
│   └── RELEASE_NOTES.md
├── tests/                 # Test files
│   ├── integration_test.py
│   ├── platform_test.py
│   ├── test_cross_platform.py
│   └── validate_features.py
├── utils/                 # Utility scripts and demos
│   ├── check_imports.py
│   ├── demo_ux_improvements.py
│   ├── hook-vgamepad.py
│   ├── inspect_vgamepad.py
│   ├── main_original.py
│   └── ui_mockup.py
├── scripts/               # Build and setup scripts
├── img/                   # Application icons and images
├── main.py               # Main application entry point
├── gp_backend.py         # Backend controller wrapper
├── platform_info.py      # Platform detection and info
├── requirements.txt      # Python dependencies
├── coopad.spec          # PyInstaller build specification
└── README.md            # This file
```

## 🤝 Contributing

This is an open-source project. Contributions are welcome!

### Development Setup
```bash
# Clone the repository
git clone https://github.com/uozer7050/v5.1.git
cd v5.1

# Install dependencies
pip install -r requirements.txt

# Run from source
python3 main.py
```

## 📄 License

See LICENSE file for details.

## 🔗 Links

- **GitHub Repository**: https://github.com/uozer7050/v5.1
- **Issues & Support**: https://github.com/uozer7050/v5.1/issues
- **Releases**: https://github.com/uozer7050/v5.1/releases

## 📅 Version History

See [CHANGELOG_TR.md](CHANGELOG_TR.md) for detailed changes (Turkish).

### Latest Version: 5.1
- Configurable UDP update rates (30/60/90 Hz)
- **Controller profile support (PS4, PS5, Xbox 360)**
- **GUI controller selection in Settings**
- Real-time network telemetry (latency, jitter)
- Enhanced security (packet validation, rate limiting)
- Improved build system for Windows and Linux
- Settings tab with network configuration
- Cross-platform compatibility improvements
- User-friendly error messages and status indicators

---

**Made with ❤️ for the gaming community**