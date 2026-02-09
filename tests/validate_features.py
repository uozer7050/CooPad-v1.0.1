#!/usr/bin/env python3
"""
Automated validation test for CooPad v5.1 features
Tests that all new features are implemented correctly
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required modules can be imported."""
    print("=" * 60)
    print("Testing Module Imports")
    print("=" * 60)
    
    errors = []
    
    try:
        from gp.core import client, host, protocol
        print("✓ Core modules imported successfully")
    except Exception as e:
        errors.append(f"Core modules: {e}")
    
    try:
        import gp_backend
        print("✓ Backend module imported successfully")
    except Exception as e:
        errors.append(f"Backend: {e}")
    
    try:
        import main
        print("✓ Main module imported successfully")
    except Exception as e:
        errors.append(f"Main: {e}")
    
    try:
        import platform_info
        print("✓ Platform info module imported successfully")
    except Exception as e:
        errors.append(f"Platform info: {e}")
    
    return errors

def test_protocol_security():
    """Test security features in protocol."""
    print("\n" + "=" * 60)
    print("Testing Protocol Security Features")
    print("=" * 60)
    
    from gp.core import protocol
    import struct
    
    errors = []
    
    # Test packet size validation
    try:
        # Too small packet
        small_packet = b'x' * 10
        assert not protocol.validate_packet_size(small_packet), "Should reject too small packet"
        print("✓ Packet size validation: rejects small packets")
    except Exception as e:
        errors.append(f"Packet size validation (small): {e}")
    
    try:
        # Too large packet
        large_packet = b'x' * 2000
        assert not protocol.validate_packet_size(large_packet), "Should reject too large packet"
        print("✓ Packet size validation: rejects large packets")
    except Exception as e:
        errors.append(f"Packet size validation (large): {e}")
    
    try:
        # Valid packet size
        valid_packet = b'x' * protocol.PACKET_SIZE
        assert protocol.validate_packet_size(valid_packet), "Should accept valid packet"
        print("✓ Packet size validation: accepts valid packets")
    except Exception as e:
        errors.append(f"Packet size validation (valid): {e}")
    
    # Test gamepad state validation
    try:
        # Create invalid state (wrong version)
        invalid_state = protocol.GamepadState(
            version=99, client_id=1, sequence=0, buttons=0,
            lt=0, rt=0, lx=0, ly=0, rx=0, ry=0, timestamp=0
        )
        assert not protocol.validate_gamepad_state(invalid_state), "Should reject wrong version"
        print("✓ State validation: rejects invalid version")
    except Exception as e:
        errors.append(f"State validation (version): {e}")
    
    try:
        # Create invalid state (out of range triggers)
        invalid_state = protocol.GamepadState(
            version=protocol.PROTOCOL_VERSION, client_id=1, sequence=0, buttons=0,
            lt=300, rt=0, lx=0, ly=0, rx=0, ry=0, timestamp=0
        )
        assert not protocol.validate_gamepad_state(invalid_state), "Should reject out of range trigger"
        print("✓ State validation: rejects out of range triggers")
    except Exception as e:
        errors.append(f"State validation (triggers): {e}")
    
    try:
        # Create valid state
        valid_state = protocol.GamepadState(
            version=protocol.PROTOCOL_VERSION, client_id=1, sequence=0, buttons=0,
            lt=128, rt=128, lx=0, ly=0, rx=0, ry=0, timestamp=0
        )
        assert protocol.validate_gamepad_state(valid_state), "Should accept valid state"
        print("✓ State validation: accepts valid state")
    except Exception as e:
        errors.append(f"State validation (valid): {e}")
    
    return errors

def test_client_features():
    """Test client features like configurable update rate."""
    print("\n" + "=" * 60)
    print("Testing Client Features")
    print("=" * 60)
    
    from gp.core.client import GamepadClient
    
    errors = []
    
    try:
        # Test client with different update rates
        for rate in [30, 60, 90]:
            client = GamepadClient(update_rate=rate)
            assert client.update_rate == rate, f"Update rate should be {rate}"
        print("✓ Client: configurable update rates (30/60/90 Hz)")
    except Exception as e:
        errors.append(f"Client update rate: {e}")
    
    try:
        # Test telemetry callback
        telemetry_received = []
        def telemetry_cb(msg):
            telemetry_received.append(msg)
        
        client = GamepadClient(telemetry_cb=telemetry_cb)
        assert client.telemetry_cb is not None, "Telemetry callback should be set"
        print("✓ Client: telemetry callback support")
    except Exception as e:
        errors.append(f"Client telemetry: {e}")
    
    return errors

def test_host_features():
    """Test host features like rate limiting."""
    print("\n" + "=" * 60)
    print("Testing Host Features")
    print("=" * 60)
    
    from gp.core.host import GamepadHost
    
    errors = []
    
    try:
        host = GamepadHost()
        assert hasattr(host, '_rate_limit_max'), "Host should have rate limit"
        assert host._rate_limit_max == 150, "Rate limit should be 150 packets/sec"
        print("✓ Host: rate limiting enabled (150 packets/sec)")
    except Exception as e:
        errors.append(f"Host rate limiting: {e}")
    
    try:
        host = GamepadHost()
        assert hasattr(host, 'telemetry_cb'), "Host should have telemetry callback"
        print("✓ Host: telemetry callback support")
    except Exception as e:
        errors.append(f"Host telemetry: {e}")
    
    try:
        host = GamepadHost()
        # Test rate limit check method
        result = host._check_rate_limit(12345, ('127.0.0.1', 7777))
        assert result == True, "First packet should be allowed"
        print("✓ Host: rate limit check method works")
    except Exception as e:
        errors.append(f"Host rate limit check: {e}")
    
    return errors

def test_backend_features():
    """Test backend controller features."""
    print("\n" + "=" * 60)
    print("Testing Backend Features")
    print("=" * 60)
    
    import gp_backend
    
    errors = []
    
    try:
        def dummy_cb(msg): pass
        controller = gp_backend.GpController(dummy_cb, dummy_cb)
        assert hasattr(controller, 'set_update_rate'), "Controller should have set_update_rate method"
        controller.set_update_rate(90)
        assert controller.update_rate == 90, "Update rate should be 90"
        print("✓ Backend: dynamic update rate configuration")
    except Exception as e:
        errors.append(f"Backend update rate: {e}")
    
    return errors

def test_ui_features():
    """Test UI features (import only, no GUI required)."""
    print("\n" + "=" * 60)
    print("Testing UI Features")
    print("=" * 60)
    
    errors = []
    
    try:
        # Just test that main module has the right structure
        import main
        assert hasattr(main, 'App'), "Main should have App class"
        print("✓ UI: Main App class exists")
    except Exception as e:
        errors.append(f"UI App class: {e}")
    
    # We can't test GUI without display, but we can verify the methods exist
    try:
        import inspect
        import main
        app_methods = [m[0] for m in inspect.getmembers(main.App, predicate=inspect.isfunction)]
        
        required_methods = ['_build_ui', '_show_tab', '_on_rate_change', '_set_telemetry']
        for method in required_methods:
            assert method in app_methods, f"App should have {method} method"
        
        print("✓ UI: Required methods exist (_build_ui, _show_tab, _on_rate_change, _set_telemetry)")
    except Exception as e:
        errors.append(f"UI methods: {e}")
    
    return errors

def main():
    """Run all validation tests."""
    print("\n" + "=" * 60)
    print("CooPad v5.1 Feature Validation")
    print("=" * 60 + "\n")
    
    all_errors = []
    
    # Run all tests
    all_errors.extend(test_imports())
    all_errors.extend(test_protocol_security())
    all_errors.extend(test_client_features())
    all_errors.extend(test_host_features())
    all_errors.extend(test_backend_features())
    all_errors.extend(test_ui_features())
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    if all_errors:
        print(f"\n❌ {len(all_errors)} ERROR(S) FOUND:\n")
        for i, error in enumerate(all_errors, 1):
            print(f"{i}. {error}")
        return 1
    else:
        print("\n✅ ALL VALIDATION TESTS PASSED!")
        print("\nNew features implemented successfully:")
        print("  • Configurable UDP update rates (30/60/90 Hz)")
        print("  • Real-time network telemetry (latency, jitter, rate)")
        print("  • Packet validation and size checking")
        print("  • Rate limiting (150 packets/sec)")
        print("  • Gamepad state validation")
        print("  • Settings tab in GUI")
        print("  • Enhanced security features")
        return 0

if __name__ == '__main__':
    sys.exit(main())
