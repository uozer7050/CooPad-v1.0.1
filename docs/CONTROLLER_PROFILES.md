# Controller Profiles Guide

CooPad now supports multiple controller profiles to ensure proper button and axis mapping for different gamepad types.

## Supported Controllers

### PlayStation 4 Controller
**Profile Name:** `PS4 Controller`

**Controller Recognition:** "PS4 Controller" in pygame

**Axes Mapping:**
- Axis 0: Left Stick X (Left → Right)
- Axis 1: Left Stick Y (Up → Down)
- Axis 2: Right Stick X (Left → Right)
- Axis 3: Right Stick Y (Up → Down)
- Axis 4: Left Trigger (Out → In)
- Axis 5: Right Trigger (Out → In)

**Button Mapping:**
- Button 0: Cross (mapped to A)
- Button 1: Circle (mapped to B)
- Button 2: Square (mapped to X)
- Button 3: Triangle (mapped to Y)
- Button 4: Share (mapped to Back)
- Button 5: PS Button
- Button 6: Options (mapped to Start)
- Button 7: Left Stick In
- Button 8: Right Stick In
- Button 9: Left Bumper
- Button 10: Right Bumper
- Button 11: D-pad Up
- Button 12: D-pad Down
- Button 13: D-pad Left
- Button 14: D-pad Right
- Button 15: Touch Pad Click

### PlayStation 5 Controller
**Profile Name:** `PS5 Controller`

**Controller Recognition:** "Sony Interactive Entertainment Wireless Controller" in pygame

**Axes Mapping:**
- Axis 0: Left Stick X (Left → Right)
- Axis 1: Left Stick Y (Up → Down)
- Axis 2: Left Trigger (Out → In)
- Axis 3: Right Stick X (Left → Right)
- Axis 4: Right Stick Y (Up → Down)
- Axis 5: Right Trigger (Out → In)

**Button Mapping:**
- Button 0: Cross (mapped to A)
- Button 1: Circle (mapped to B)
- Button 2: Square (mapped to X)
- Button 3: Triangle (mapped to Y)
- Button 4: Left Bumper
- Button 5: Right Bumper
- Button 6: Left Trigger (button press)
- Button 7: Right Trigger (button press)
- Button 8: Share (mapped to Back)
- Button 9: Options (mapped to Start)
- Button 10: PS Button
- Button 11: Left Stick In
- Button 12: Right Stick In

**D-pad:** Uses Hat (X/Y axis) instead of buttons

### Xbox 360 Controller
**Profile Name:** `Xbox 360 Controller`

**Controller Recognition:** "Controller (XBOX 360 For Windows)" in pygame

**Axes Mapping:**
- Axis 0: Left Stick X (Left → Right)
- Axis 1: Left Stick Y (Up → Down)
- Axis 2: Triggers (RT → LT, combined axis)
- Axis 3: Right Stick Y (Up → Down)
- Axis 4: Right Stick X (Left → Right)

**Button Mapping:**
- Button 0: A
- Button 1: B
- Button 2: X
- Button 3: Y
- Button 4: Left Bumper
- Button 5: Right Bumper
- Button 6: Back
- Button 7: Start
- Button 8: Left Stick In
- Button 9: Right Stick In

**D-pad:** Uses Hat (X/Y axis) instead of buttons

**Special Note:** Left and Right triggers share a single axis (Axis 2). The profile automatically converts this to separate trigger values.

### Generic Controller
**Profile Name:** `Generic`

**Description:** Default fallback profile that works with most standard controllers

**Axes Mapping:**
- Axis 0: Left Stick X
- Axis 1: Left Stick Y
- Axis 2: Right Stick X
- Axis 3: Right Stick Y

**Button Mapping:** Standard button order (0-13)

**D-pad:** Supports both buttons and hat

## How to Select a Controller Profile

1. Open CooPad
2. Go to the **Settings** tab
3. Find the **Controller Profile** section
4. Select your controller type from the dropdown menu
5. The change takes effect when you start/restart the client

## Technical Details

### Protocol Mapping

All controller profiles map to the same internal protocol for compatibility:

**Protocol Button Bits:**
- `0x0001`: D-pad Up
- `0x0002`: D-pad Down
- `0x0004`: D-pad Left
- `0x0008`: D-pad Right
- `0x0010`: Start
- `0x0020`: Back/Select
- `0x0040`: Left Thumb (L3)
- `0x0080`: Right Thumb (R3)
- `0x0100`: Left Shoulder (L1/LB)
- `0x0200`: Right Shoulder (R1/RB)
- `0x1000`: A (Cross on PS)
- `0x2000`: B (Circle on PS)
- `0x4000`: X (Square on PS)
- `0x8000`: Y (Triangle on PS)

**Axes:**
- Left/Right Stick: -32768 to 32767 (0 = center)
- Triggers: 0 to 255 (0 = released)

### Creating Custom Profiles

If you need to create a custom profile for your controller:

1. Edit `/gp/core/controller_profiles.py`
2. Create a new class that inherits from `ControllerProfile`
3. Override `get_axes_mapping()` and `get_button_mapping()` methods
4. Add your profile to the `CONTROLLER_PROFILES` dictionary
5. Restart CooPad

Example:
```python
class MyCustomProfile(ControllerProfile):
    def __init__(self):
        super().__init__()
        self.name = "My Custom Controller"
        self.description = "Custom controller description"
    
    def get_axes_mapping(self):
        return {
            'left_x': 0,
            'left_y': 1,
            'right_x': 2,
            'right_y': 3,
            'left_trigger': 4,
            'right_trigger': 5,
        }
    
    def get_button_mapping(self):
        return {
            0: 0x1000,  # Button 0 → A
            1: 0x2000,  # Button 1 → B
            # ... etc
        }
```

## Troubleshooting

### Wrong Button Mapping
- Make sure you selected the correct controller profile in Settings
- Restart the client after changing the profile
- Some third-party controllers may need the Generic profile

### Triggers Not Working
- PS4/PS5: Triggers should work automatically on their dedicated axes
- Xbox 360: Triggers share an axis and are automatically split
- If triggers don't work, try the Generic profile

### D-pad Not Working
- PS5/Xbox 360: D-pad is on the hat (automatically detected)
- PS4: D-pad is on buttons 11-14
- Some controllers may support both methods

### Controller Not Detected
- Ensure controller is properly connected
- Check if pygame can detect it: `python -m pygame.examples.joystick`
- Install pygame-ce for Python 3.12+: `pip install pygame-ce`
- Try unplugging and reconnecting the controller

## pygame 2.x vs pygame 1.x

The profiles are designed for pygame 2.x (and pygame-ce). If you're using pygame 1.x, some mappings may be different:
- Button indices might vary
- Axis indices might be ordered differently
- Try the Generic profile if issues occur

## Related Files

- `/gp/core/controller_profiles.py` - Profile definitions
- `/gp/core/client.py` - Profile usage in client
- `/main.py` - GUI controller selection
- `/gp_backend.py` - Backend profile management
