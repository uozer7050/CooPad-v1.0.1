"""
Controller profiles for different gamepad types.

This module defines controller mappings for various gamepad types to properly
convert pygame axis/button indices to the protocol button bits.
"""


class ControllerProfile:
    """Base class for controller profiles."""
    
    def __init__(self):
        self.name = "Generic"
        self.description = "Generic controller mapping"
    
    def get_axes_mapping(self):
        """
        Returns a dictionary mapping logical stick names to pygame axis indices.
        
        Returns:
            dict: {
                'left_x': axis_index,
                'left_y': axis_index,
                'right_x': axis_index,
                'right_y': axis_index,
                'left_trigger': axis_index or None,
                'right_trigger': axis_index or None,
            }
        """
        return {
            'left_x': 0,
            'left_y': 1,
            'right_x': 2,
            'right_y': 3,
            'left_trigger': 4,
            'right_trigger': 5,
        }
    
    def get_button_mapping(self):
        """
        Returns a dictionary mapping pygame button indices to protocol button bits.
        
        Protocol bits:
            0x0001: DPad Up
            0x0002: DPad Down
            0x0004: DPad Left
            0x0008: DPad Right
            0x0010: Start
            0x0020: Back/Select
            0x0040: Left Thumb
            0x0080: Right Thumb
            0x0100: Left Shoulder
            0x0200: Right Shoulder
            0x1000: A (Cross on PS)
            0x2000: B (Circle on PS)
            0x4000: X (Square on PS)
            0x8000: Y (Triangle on PS)
        
        Returns:
            dict: {pygame_button_index: protocol_bit}
        """
        return {
            0: 0x1000,    # Button 0 (A) → bit 12
            1: 0x2000,    # Button 1 (B) → bit 13
            2: 0x4000,    # Button 2 (X) → bit 14
            3: 0x8000,    # Button 3 (Y) → bit 15
            4: 0x0100,    # Button 4 (Left Shoulder) → bit 8
            5: 0x0200,    # Button 5 (Right Shoulder) → bit 9
            6: 0x0020,    # Button 6 (Back/Select) → bit 5
            7: 0x0010,    # Button 7 (Start) → bit 4
            8: 0x0040,    # Button 8 (Left Thumb) → bit 6
            9: 0x0080,    # Button 9 (Right Thumb) → bit 7
            10: 0x0001,   # Button 10 (DPad Up) → bit 0
            11: 0x0002,   # Button 11 (DPad Down) → bit 1
            12: 0x0004,   # Button 12 (DPad Left) → bit 2
            13: 0x0008,   # Button 13 (DPad Right) → bit 3
        }
    
    def uses_hat_for_dpad(self):
        """Returns True if this controller uses hat for D-pad instead of buttons."""
        return False
    
    def invert_y_axes(self):
        """
        Returns True if Y axes need to be inverted (multiplied by -1) when
        converting from pygame to XInput convention.
        
        Most controllers report Y axis as Up→Down (-1=Up, +1=Down), which
        needs inversion for XInput (positive=up). Joy-Cons report Y axis
        as Down→Up (-1=Down, +1=Up), which already matches XInput convention
        and should NOT be inverted.
        """
        return True


class PS4ControllerProfile(ControllerProfile):
    """PlayStation 4 controller profile (pygame 2.x)."""
    
    def __init__(self):
        super().__init__()
        self.name = "PS4 Controller"
        self.description = "PlayStation 4 Controller (6 axes, 16 buttons)"
    
    def get_axes_mapping(self):
        """
        PS4 Controller axes:
            Axis 0: Left Stick X (Left -> Right)
            Axis 1: Left Stick Y (Up -> Down)
            Axis 2: Right Stick X (Left -> Right)
            Axis 3: Right Stick Y (Up -> Down)
            Axis 4: Left Trigger (Out -> In)
            Axis 5: Right Trigger (Out -> In)
        """
        return {
            'left_x': 0,
            'left_y': 1,
            'right_x': 2,
            'right_y': 3,
            'left_trigger': 4,
            'right_trigger': 5,
        }
    
    def get_button_mapping(self):
        """
        PS4 Controller buttons:
            Button 0: Cross (A)
            Button 1: Circle (B)
            Button 2: Square (X)
            Button 3: Triangle (Y)
            Button 4: Share (Back)
            Button 5: PS Button (Guide)
            Button 6: Options (Start)
            Button 7: Left Stick In
            Button 8: Right Stick In
            Button 9: Left Bumper
            Button 10: Right Bumper
            Button 11: D-pad Up
            Button 12: D-pad Down
            Button 13: D-pad Left
            Button 14: D-pad Right
            Button 15: Touch Pad Click
        """
        return {
            0: 0x1000,    # Cross → A
            1: 0x2000,    # Circle → B
            2: 0x4000,    # Square → X
            3: 0x8000,    # Triangle → Y
            4: 0x0020,    # Share → Back
            6: 0x0010,    # Options → Start
            7: 0x0040,    # L. Stick In → Left Thumb
            8: 0x0080,    # R. Stick In → Right Thumb
            9: 0x0100,    # Left Bumper → Left Shoulder
            10: 0x0200,   # Right Bumper → Right Shoulder
            11: 0x0001,   # D-pad Up
            12: 0x0002,   # D-pad Down
            13: 0x0004,   # D-pad Left
            14: 0x0008,   # D-pad Right
        }


class PS5ControllerProfile(ControllerProfile):
    """PlayStation 5 controller profile (pygame 2.x)."""
    
    def __init__(self):
        super().__init__()
        self.name = "PS5 Controller"
        self.description = "PlayStation 5 Controller (6 axes, 13 buttons, 1 hat)"
    
    def get_axes_mapping(self):
        """
        PS5 Controller axes:
            Axis 0: Left Stick X (Left -> Right)
            Axis 1: Left Stick Y (Up -> Down)
            Axis 2: Left Trigger (Out -> In)
            Axis 3: Right Stick X (Left -> Right)
            Axis 4: Right Stick Y (Up -> Down)
            Axis 5: Right Trigger (Out -> In)
        """
        return {
            'left_x': 0,
            'left_y': 1,
            'right_x': 3,
            'right_y': 4,
            'left_trigger': 2,
            'right_trigger': 5,
        }
    
    def get_button_mapping(self):
        """
        PS5 Controller buttons:
            Button 0: Cross (A)
            Button 1: Circle (B)
            Button 2: Square (X)
            Button 3: Triangle (Y)
            Button 4: Left Bumper
            Button 5: Right Bumper
            Button 6: Left Trigger (button)
            Button 7: Right Trigger (button)
            Button 8: Share
            Button 9: Options
            Button 10: PS Button
            Button 11: Left Stick In
            Button 12: Right Stick In
        """
        return {
            0: 0x1000,    # Cross → A
            1: 0x2000,    # Circle → B
            2: 0x4000,    # Square → X
            3: 0x8000,    # Triangle → Y
            4: 0x0100,    # Left Bumper → Left Shoulder
            5: 0x0200,    # Right Bumper → Right Shoulder
            8: 0x0020,    # Share → Back
            9: 0x0010,    # Options → Start
            11: 0x0040,   # Left Stick In → Left Thumb
            12: 0x0080,   # Right Stick In → Right Thumb
        }
    
    def uses_hat_for_dpad(self):
        """PS5 controller uses hat for D-pad."""
        return True


class Xbox360ControllerProfile(ControllerProfile):
    """Xbox 360 controller profile (pygame 2.x / pygame-ce)."""
    
    def __init__(self):
        super().__init__()
        self.name = "Xbox 360 Controller"
        self.description = "Xbox 360 Controller (6 axes, 11 buttons, 1 hat)"
    
    def get_axes_mapping(self):
        """
        Xbox 360 Controller axes (pygame 2.x):
            Axis 0: Left Stick X (Left -> Right)
            Axis 1: Left Stick Y (Up -> Down)
            Axis 2: Left Trigger (Out -> In)
            Axis 3: Right Stick X (Left -> Right)
            Axis 4: Right Stick Y (Up -> Down)
            Axis 5: Right Trigger (Out -> In)
        """
        return {
            'left_x': 0,
            'left_y': 1,
            'right_x': 3,
            'right_y': 4,
            'left_trigger': 2,
            'right_trigger': 5,
        }
    
    def get_button_mapping(self):
        """
        Xbox 360 Controller buttons (pygame 2.x):
            Button 0: A
            Button 1: B
            Button 2: X
            Button 3: Y
            Button 4: Left Bumper
            Button 5: Right Bumper
            Button 6: Back
            Button 7: Start
            Button 8: Left Stick In
            Button 9: Right Stick In
            Button 10: Guide
        """
        return {
            0: 0x1000,    # A
            1: 0x2000,    # B
            2: 0x4000,    # X
            3: 0x8000,    # Y
            4: 0x0100,    # Left Bumper → Left Shoulder
            5: 0x0200,    # Right Bumper → Right Shoulder
            6: 0x0020,    # Back → Back/Select
            7: 0x0010,    # Start
            8: 0x0040,    # Left Stick In → Left Thumb
            9: 0x0080,    # Right Stick In → Right Thumb
        }
    
    def uses_hat_for_dpad(self):
        """Xbox 360 controller uses hat for D-pad."""
        return True


class NintendoSwitchJoyConProfile(ControllerProfile):
    """
    Nintendo Switch Joy-Con (Left or Right) profile (pygame 2.x).
    
    Note: Each Joy-Con has only ONE analog stick. This profile maps the single
    stick to both left and right stick inputs in the protocol, so the stick
    will control whichever stick the game expects. When using a single Joy-Con,
    games expecting dual-stick input will only receive input from one stick.
    
    For full dual-stick support, use the Nintendo Switch Pro Controller profile
    or pair both Joy-Cons (though pygame may recognize them as separate devices).
    """
    
    def __init__(self):
        super().__init__()
        self.name = "Nintendo Switch Joy-Con"
        self.description = "Nintendo Switch Joy-Con Left/Right (4 axes, 11 buttons, 0 hats)"
    
    def get_axes_mapping(self):
        """
        Nintendo Switch Joy-Con axes:
            Both Left and Right Joy-Cons have:
            X Axis: Left -> Right
            Y Axis: Down -> Up (inverted from typical)
            
            Note: The Joy-Cons have 4 axes but only 2 are used for the stick.
            Since each Joy-Con has only one physical stick, we map it to both
            left and right stick positions in the protocol.
        """
        return {
            'left_x': 0,    # Single stick X axis
            'left_y': 1,    # Single stick Y axis (inverted)
            'right_x': 0,   # No right stick, use left stick
            'right_y': 1,   # No right stick, use left stick
            'left_trigger': None,  # No analog triggers
            'right_trigger': None,  # No analog triggers
        }
    
    def get_button_mapping(self):
        """
        Nintendo Switch Joy-Con button mapping (combined Left + Right):
        
        Left Joy-Con:
            Button 0: D-pad Up
            Button 1: D-pad Down
            Button 2: D-pad Left
            Button 3: D-pad Right
            Button 4: SL (mapped as Left Shoulder)
            Button 5: SR (mapped as Right Shoulder)
            Button 8: - (Minus)
            Button 10: Stick In
            Button 13: Capture
            Button 14: L
            Button 15: ZL
            
        Right Joy-Con:
            Button 0: A
            Button 1: B
            Button 2: X
            Button 3: Y
            Button 4: SL (mapped as Left Shoulder)
            Button 5: SR (mapped as Right Shoulder)
            Button 9: + (Plus)
            Button 11: Stick In
            Button 12: Home
            Button 14: R
            Button 15: ZR
            
        Note: Buttons 4/5 (SL/SR) and 14/15 (L/R, ZL/ZR) serve different purposes
        depending on Joy-Con orientation. When used standalone, SL/SR act as
        shoulders. When paired, L/R/ZL/ZR are the primary shoulder buttons.
        This mapping prioritizes the paired configuration.
        """
        return {
            # Right Joy-Con face buttons (when right is primary)
            0: 0x1000,    # A (or D-pad Up on Left Joy-Con)
            1: 0x2000,    # B (or D-pad Down on Left Joy-Con)
            2: 0x4000,    # X (or D-pad Left on Left Joy-Con)
            3: 0x8000,    # Y (or D-pad Right on Left Joy-Con)
            
            # SL/SR buttons (when Joy-Con used standalone)
            4: 0x0100,    # SL → Left Shoulder
            5: 0x0200,    # SR → Right Shoulder
            
            # System buttons
            8: 0x0020,    # - (Left Joy-Con) → Back/Select
            9: 0x0010,    # + (Right Joy-Con) → Start
            
            # Stick buttons
            10: 0x0040,   # Stick In (Left Joy-Con) → Left Thumb
            11: 0x0080,   # Stick In (Right Joy-Con) → Right Thumb
            
            # L/R and ZL/ZR buttons (when Joy-Cons paired)
            # Note: These overlap with buttons 4/5 in the protocol.
            # Games will receive shoulder button input from either SL/SR or L/R/ZL/ZR
            14: 0x0100,   # L/R → Left Shoulder (same as button 4)
            15: 0x0200,   # ZL/ZR → Right Shoulder (same as button 5)
        }
    
    def invert_y_axes(self):
        """
        Joy-Con Y axis is reported as Down→Up (-1=Down, +1=Up) by pygame,
        which already matches XInput convention (positive=up).
        No inversion needed.
        """
        return False


class NintendoSwitchProControllerProfile(ControllerProfile):
    """Nintendo Switch Pro Controller profile (pygame 2.x)."""
    
    def __init__(self):
        super().__init__()
        self.name = "Nintendo Switch Pro Controller"
        self.description = "Nintendo Switch Pro Controller (6 axes, 16 buttons, 0 hats)"
    
    def get_axes_mapping(self):
        """
        Nintendo Switch Pro Controller axes:
            Axis 0: Left Stick X (Left -> Right)
            Axis 1: Left Stick Y (Up -> Down)
            Axis 2: Right Stick X (Left -> Right)
            Axis 3: Right Stick Y (Up -> Down)
            Axis 4: Left Trigger (Out -> In)
            Axis 5: Right Trigger (Out -> In)
        """
        return {
            'left_x': 0,
            'left_y': 1,
            'right_x': 2,
            'right_y': 3,
            'left_trigger': 4,
            'right_trigger': 5,
        }
    
    def get_button_mapping(self):
        """
        Nintendo Switch Pro Controller buttons:
            Button 0: A
            Button 1: B
            Button 2: X
            Button 3: Y
            Button 4: - (Minus)
            Button 5: Home
            Button 6: + (Plus)
            Button 7: Left Stick In
            Button 8: Right Stick In
            Button 9: Left Bumper
            Button 10: Right Bumper
            Button 11: D-pad Up
            Button 12: D-pad Down
            Button 13: D-pad Left
            Button 14: D-pad Right
            Button 15: Capture
        """
        return {
            0: 0x1000,    # A
            1: 0x2000,    # B
            2: 0x4000,    # X
            3: 0x8000,    # Y
            4: 0x0020,    # - (Minus) → Back/Select
            6: 0x0010,    # + (Plus) → Start
            7: 0x0040,    # Left Stick In → Left Thumb
            8: 0x0080,    # Right Stick In → Right Thumb
            9: 0x0100,    # Left Bumper → Left Shoulder
            10: 0x0200,   # Right Bumper → Right Shoulder
            11: 0x0001,   # D-pad Up
            12: 0x0002,   # D-pad Down
            13: 0x0004,   # D-pad Left
            14: 0x0008,   # D-pad Right
        }


# Dictionary of all available profiles
CONTROLLER_PROFILES = {
    'generic': ControllerProfile(),
    'ps4': PS4ControllerProfile(),
    'ps5': PS5ControllerProfile(),
    'xbox360': Xbox360ControllerProfile(),
    'switch_joycon': NintendoSwitchJoyConProfile(),
    'switch_pro': NintendoSwitchProControllerProfile(),
}


def get_profile(profile_name):
    """
    Get a controller profile by name.
    
    Args:
        profile_name: Profile name key ('generic', 'ps4', 'ps5', 'xbox360', 'switch_joycon', 'switch_pro')
    
    Returns:
        ControllerProfile: The requested profile, or generic if not found
    """
    return CONTROLLER_PROFILES.get(profile_name, CONTROLLER_PROFILES['generic'])


def get_profile_names():
    """
    Get a list of all available profile names.
    
    Returns:
        list: List of profile display names
    """
    return [profile.name for profile in CONTROLLER_PROFILES.values()]


def get_profile_by_display_name(display_name):
    """
    Get a controller profile by its display name.
    
    Args:
        display_name: The display name of the profile
    
    Returns:
        str: The profile key, or 'generic' if not found
    """
    for key, profile in CONTROLLER_PROFILES.items():
        if profile.name == display_name:
            return key
    return 'generic'
