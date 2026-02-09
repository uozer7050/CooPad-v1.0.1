#!/usr/bin/env python3
"""
Integration test for controller profiles.

This test verifies that controller profiles work correctly with the client system.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gp.core.controller_profiles import (
    CONTROLLER_PROFILES,
    get_profile,
    get_profile_names,
    get_profile_by_display_name
)
from gp.core.client import GamepadClient


def test_profile_imports():
    """Test that all profiles can be imported."""
    print("Testing profile imports...")
    assert len(CONTROLLER_PROFILES) == 6, "Should have 6 profiles"
    
    for key in ['generic', 'ps4', 'ps5', 'xbox360', 'switch_joycon', 'switch_pro']:
        assert key in CONTROLLER_PROFILES, f"Missing profile: {key}"
        profile = CONTROLLER_PROFILES[key]
        assert profile.name is not None
        assert profile.description is not None
    
    print("✓ All profiles import correctly")


def test_profile_mappings():
    """Test that profiles have valid mappings."""
    print("\nTesting profile mappings...")
    
    for key, profile in CONTROLLER_PROFILES.items():
        # Test axes mapping
        axes_map = profile.get_axes_mapping()
        assert 'left_x' in axes_map
        assert 'left_y' in axes_map
        assert 'right_x' in axes_map
        assert 'right_y' in axes_map
        
        # Test button mapping
        button_map = profile.get_button_mapping()
        assert len(button_map) > 0, f"Profile {key} has no button mappings"
        
        # Verify button values are valid protocol bits
        for btn_idx, bit_value in button_map.items():
            assert isinstance(btn_idx, int)
            assert isinstance(bit_value, int)
            assert bit_value > 0 and bit_value <= 0xFFFF
        
        print(f"✓ {profile.name} mappings are valid")


def test_specific_profiles():
    """Test specific profile configurations."""
    print("\nTesting specific profiles...")
    
    # PS4: Should have separate trigger axes
    ps4 = get_profile('ps4')
    ps4_axes = ps4.get_axes_mapping()
    assert ps4_axes['left_trigger'] == 4
    assert ps4_axes['right_trigger'] == 5
    assert not ps4.uses_hat_for_dpad()
    print("✓ PS4 profile has correct trigger axes")
    
    # PS5: Should have different axis layout and use hat
    ps5 = get_profile('ps5')
    ps5_axes = ps5.get_axes_mapping()
    assert ps5_axes['right_x'] == 3
    assert ps5_axes['right_y'] == 4
    assert ps5_axes['left_trigger'] == 2
    assert ps5.uses_hat_for_dpad()
    print("✓ PS5 profile has correct axis layout")
    
    # Xbox 360: Should have combined triggers and use hat
    xbox = get_profile('xbox360')
    xbox_axes = xbox.get_axes_mapping()
    assert xbox_axes['left_trigger'] is None
    assert xbox_axes['right_trigger'] is None
    assert xbox.uses_hat_for_dpad()
    assert hasattr(xbox, 'get_trigger_from_axis')
    print("✓ Xbox 360 profile has combined triggers")
    
    # Nintendo Switch Joy-Con: Should have single stick mapped to both left and right
    joycon = get_profile('switch_joycon')
    joycon_axes = joycon.get_axes_mapping()
    assert joycon_axes['left_x'] == 0
    assert joycon_axes['left_y'] == 1
    assert joycon_axes['left_trigger'] is None
    assert joycon_axes['right_trigger'] is None
    assert not joycon.uses_hat_for_dpad()
    print("✓ Nintendo Switch Joy-Con profile has correct configuration")
    
    # Nintendo Switch Pro Controller: Should have full dual-stick and separate triggers
    switch_pro = get_profile('switch_pro')
    switch_pro_axes = switch_pro.get_axes_mapping()
    assert switch_pro_axes['left_x'] == 0
    assert switch_pro_axes['left_y'] == 1
    assert switch_pro_axes['right_x'] == 2
    assert switch_pro_axes['right_y'] == 3
    assert switch_pro_axes['left_trigger'] == 4
    assert switch_pro_axes['right_trigger'] == 5
    assert not switch_pro.uses_hat_for_dpad()
    print("✓ Nintendo Switch Pro Controller profile has correct configuration")


def test_client_integration():
    """Test that clients can use profiles."""
    print("\nTesting client integration...")
    
    for profile_key in ['generic', 'ps4', 'ps5', 'xbox360', 'switch_joycon', 'switch_pro']:
        try:
            client = GamepadClient(
                target_ip='127.0.0.1',
                port=7777,
                controller_profile=profile_key
            )
            assert client.controller_profile is not None
            assert client.controller_profile.name is not None
            print(f"✓ Client created with {client.controller_profile.name}")
        except Exception as e:
            print(f"✗ Failed to create client with {profile_key}: {e}")
            raise


def test_display_name_conversion():
    """Test display name to key conversion."""
    print("\nTesting display name conversion...")
    
    profile_names = get_profile_names()
    assert len(profile_names) == 6
    
    for display_name in profile_names:
        key = get_profile_by_display_name(display_name)
        assert key in CONTROLLER_PROFILES
        profile = get_profile(key)
        assert profile.name == display_name
        print(f"✓ {display_name} → {key}")


def test_xbox_trigger_extraction():
    """Test Xbox 360 trigger extraction from combined axis."""
    print("\nTesting Xbox 360 trigger extraction...")
    
    xbox = get_profile('xbox360')
    
    # Test cases: (axis_value, expected_lt, expected_rt)
    test_cases = [
        (-1.0, 255, 0, "LT fully pressed"),
        (1.0, 0, 255, "RT fully pressed"),
        (0.0, 0, 0, "Neither pressed"),
        (-0.5, 127, 0, "LT half pressed"),
        (0.5, 0, 127, "RT half pressed"),
    ]
    
    for axis_val, expected_lt, expected_rt, description in test_cases:
        lt, rt = xbox.get_trigger_from_axis(axis_val)
        assert abs(lt - expected_lt) <= 1, f"LT mismatch for {description}"
        assert abs(rt - expected_rt) <= 1, f"RT mismatch for {description}"
        print(f"✓ {description}: axis={axis_val:.1f} → LT={lt}, RT={rt}")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Controller Profile Integration Tests")
    print("=" * 60)
    
    try:
        test_profile_imports()
        test_profile_mappings()
        test_specific_profiles()
        test_client_integration()
        test_display_name_conversion()
        test_xbox_trigger_extraction()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        return 0
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"✗ TEST FAILED: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
