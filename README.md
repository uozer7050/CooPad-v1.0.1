# CooPad

![License](https://img.shields.io/badge/license-MIT-green)



![MainPhoto](img/mainphoto.jpg)




![SecondPhoto](img/543521876-2f59bfaa-b5b1-43af-a9b6-7a827cb36bdf.png)



**Remote gamepad application for gaming over network**

CooPad allows you to use a physical gamepad connected to one computer (Client) to control games on another computer (Host) over a local network or VPN. Perfect for couch gaming, game streaming, or playing with friends remotely.

🖥️ **100% open-source project. Contributions, reviews, and improvements are welcome, and some features or edge cases may still be missing.**

## 🎮 Features

- **Controller Profiles**: Built-in support for PS4, PS5, Xbox 360, Nintendo Switch (Joy-Con and Pro Controller), and generic controllers
- **Low Latency**: 1-20ms on local networks, optimized for real-time gaming
- **Configurable Update Rates**: Choose between 30Hz, 60Hz, or 90Hz for optimal performance
- **Real-Time Telemetry**: Monitor latency, jitter, and packet rates
- **Smart Platform Detection**: Automatically detects your OS and available drivers
- **User-Friendly Interface**: Clean GUI with helpful status indicators and setup guides
- **Advanced Security**: Comprehensive protection with rate limiting, IP filtering, and automatic threat response

## 🫀 NEW v1.0.2 UPDATE

- **Multi‑Gamepad Co‑op: Add up to 4 remote players as separate virtual controllers** : Adds optional new mode so remote players appear as independent virtual controllers on the Host, preventing input mixing during local co‑op play.
- **Automatic ViGEmBus recovery:** Host startup failures caused by ViGEmBus initialization now automatically retry within 2 seconds and show feedback in the console.
- **Controller mapping fixes:** Improved controller mapping stability across different controller types.
- **Improved signal stability:** Users are now required to select a controller profile and the signal update rate, ensuring a smoother and more reliable experience.

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
     - Nintendo Switch Joy-Con
     - Nintendo Switch Pro Controller
     - Generic (for other controllers)

   - Choose update rate based on your network and desired input responsiveness
     - 30 Hz: Lower bandwidth, suitable for slower networks
     - 60 Hz: Recommended for most users
     - 90 Hz: High performance for low-latency networks

   
   
   ![SecondPhoto](img/543518523-01f86827-a8f5-4fe8-887a-ad81e4b2da94.png)

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
  - Reboot your computer (recommended)
    
### Client Requirements (Windows)
- **pygame-ce**: For reading physical gamepad input (pygame-ce 2.4+ required for Python 3.12+)
- **Physical gamepad**: USB or Bluetooth connected (PS4, PS5, Xbox 360, or generic)
- Client can run without a physical gamepad (sends test data)

**Note**: If you have Python 3.12 or newer, pygame-ce (Community Edition) is required instead of the legacy pygame package.

## 🎮 Controller Support

CooPad includes built-in profiles for popular controllers:

- **PlayStation 4 Controller**: Proper axis and button mapping for DS4  
- **PlayStation 5 Controller**: DualSense support with hat-based D-pad  
- **Xbox 360 Controller**: Correct mapping including combined trigger axis  
- **Nintendo Switch Joy-Con**: Left and Right Joy-Con supported individually, with correct button mapping  
- **Nintendo Switch Pro Controller**: Full Pro Controller mapping
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

CooPad includes comprehensive security features to protect against various attacks, especially DoS (Denial of Service):

### Multi-Layer Protection
- **Token Bucket Rate Limiting**: Advanced burst protection (120 packets/sec per client, 20 burst capacity)
- **IP-Based Rate Limiting**: Limits total packets per IP address (200 packets/sec)
- **Connection Limits**: Maximum 3 simultaneous clients per IP address
- **Automatic Blocking**: Auto-blocks clients after 5 security violations

### Attack Prevention
- **Timestamp Validation**: Prevents replay attacks (5-second max packet age)
- **Packet Validation**: Size and content validation for all packets
- **Duplicate Detection**: Sequence number tracking prevents packet replay
- **Input Sanitization**: Gamepad values clamped to valid ranges

### Monitoring & Response
- **Security Event Logging**: Tracks all security-related events
- **Manual IP Blocking**: Administrators can block/unblock IPs
- **IP Whitelist Support**: Optional whitelist for trusted sources
- **Real-time Statistics**: Monitor active clients, blocked IPs, and violations

For detailed security documentation, see [SECURITY.md](SECURITY.md)

### Security Best Practices
1. **Use VPN** for remote connections (ZeroTier, Tailscale, WireGuard)
2. **Enable Firewall** and only open UDP port 7777
3. **Monitor Logs** regularly for suspicious activity
4. **Keep Updated** to get latest security patches

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

Output will be in the `dist/` directory.

## 🐛 Troubleshooting

### Host Won't Start
**Windows:**
- Install ViGEm Bus Driver from official releases
- Restart computer after driver installation
- Run as Administrator if needed

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
- ✅ Windows (Host + Client)

### Virtual Gamepad
- **Windows**: ViGEm Bus Driver (Xbox 360 emulation)
- **Format**: Full Xbox 360 controller layout



---

**Made with ❤️ for the gaming community**
