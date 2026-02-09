#!/usr/bin/env python3
"""
Simulated cross-platform integration test
Tests various scenarios including cross-platform client-host connections
"""
import sys
import time
import threading
from gp.core.host import GamepadHost
from gp.core.client import GamepadClient
from gp.core.protocol import make_state_from_inputs, pack, unpack


def test_host_client_local():
    """Test host and client on same machine"""
    print("\n=== Test 1: Local Host + Client ===")
    
    host_msgs = []
    client_msgs = []
    
    def host_cb(msg):
        host_msgs.append(msg)
        print(f"  HOST: {msg}")
    
    def client_cb(msg):
        client_msgs.append(msg)
        print(f"  CLIENT: {msg}")
    
    # Start host
    host = GamepadHost(bind_ip='127.0.0.1', port=17777, status_cb=host_cb)
    host.start()
    time.sleep(0.3)
    
    # Start client
    client = GamepadClient(target_ip='127.0.0.1', port=17777, status_cb=client_cb)
    client.start()
    time.sleep(1.0)
    
    # Stop both
    client.stop()
    host.stop()
    time.sleep(0.3)
    
    # Verify
    assert any('listening' in m.lower() for m in host_msgs), "Host should be listening"
    assert any('sending' in m.lower() for m in client_msgs), "Client should be sending"
    assert any('owner' in m.lower() for m in host_msgs), "Host should receive packets"
    
    print("  ✓ Test passed")


def test_protocol_encoding():
    """Test protocol encoding/decoding"""
    print("\n=== Test 2: Protocol Encoding ===")
    
    # Create a test state
    state = make_state_from_inputs(
        client_id=12345,
        seq=100,
        buttons=0x1234,
        lt=128,
        rt=255,
        lx=-32768,
        ly=32767,
        rx=0,
        ry=-16384
    )
    
    # Pack and unpack
    data = pack(state)
    decoded = unpack(data)
    
    # Verify
    assert decoded.client_id == 12345, "Client ID mismatch"
    assert decoded.sequence == 100, "Sequence mismatch"
    assert decoded.buttons == 0x1234, "Buttons mismatch"
    assert decoded.lt == 128, "Left trigger mismatch"
    assert decoded.rt == 255, "Right trigger mismatch"
    assert decoded.lx == -32768, "Left stick X mismatch"
    assert decoded.ly == 32767, "Left stick Y mismatch"
    assert decoded.rx == 0, "Right stick X mismatch"
    assert decoded.ry == -16384, "Right stick Y mismatch"
    
    print("  ✓ Test passed")


def test_multiple_clients():
    """Test host with multiple clients (only first client is accepted)"""
    print("\n=== Test 3: Multiple Clients (Ownership) ===")
    
    host_msgs = []
    
    def host_cb(msg):
        host_msgs.append(msg)
        print(f"  HOST: {msg}")
    
    # Start host
    host = GamepadHost(bind_ip='127.0.0.1', port=17778, status_cb=host_cb)
    host.start()
    time.sleep(0.3)
    
    # Start first client
    client1 = GamepadClient(target_ip='127.0.0.1', port=17778, client_id=1000, status_cb=lambda m: None)
    client1.start()
    time.sleep(0.5)
    
    # Start second client
    client2 = GamepadClient(target_ip='127.0.0.1', port=17778, client_id=2000, status_cb=lambda m: None)
    client2.start()
    time.sleep(0.5)
    
    # Stop all
    client1.stop()
    client2.stop()
    host.stop()
    time.sleep(0.3)
    
    # Verify - host should accept first client
    assert any('owner set to 1000' in m for m in host_msgs), "Host should accept first client"
    
    print("  ✓ Test passed - Host correctly implements ownership")


def test_packet_sequence():
    """Test packet sequence handling"""
    print("\n=== Test 4: Packet Sequence ===")
    
    # Create states with different sequences
    state1 = make_state_from_inputs(client_id=100, seq=1, buttons=0, lt=0, rt=0, lx=0, ly=0, rx=0, ry=0)
    state2 = make_state_from_inputs(client_id=100, seq=2, buttons=0, lt=0, rt=0, lx=0, ly=0, rx=0, ry=0)
    state3 = make_state_from_inputs(client_id=100, seq=1, buttons=0, lt=0, rt=0, lx=0, ly=0, rx=0, ry=0)  # duplicate
    
    assert state1.sequence == 1
    assert state2.sequence == 2
    assert state3.sequence == 1  # same as state1
    
    print("  ✓ Test passed")


def test_button_mapping():
    """Test button bit mapping"""
    print("\n=== Test 5: Button Mapping ===")
    
    # Test individual buttons
    buttons = {
        'DPAD_UP': 0x0001,
        'DPAD_DOWN': 0x0002,
        'DPAD_LEFT': 0x0004,
        'DPAD_RIGHT': 0x0008,
        'START': 0x0010,
        'BACK': 0x0020,
        'LEFT_THUMB': 0x0040,
        'RIGHT_THUMB': 0x0080,
        'LEFT_SHOULDER': 0x0100,
        'RIGHT_SHOULDER': 0x0200,
        'A': 0x1000,
        'B': 0x2000,
        'X': 0x4000,
        'Y': 0x8000,
    }
    
    for name, bit in buttons.items():
        state = make_state_from_inputs(
            client_id=1, seq=1, buttons=bit,
            lt=0, rt=0, lx=0, ly=0, rx=0, ry=0
        )
        assert state.buttons & bit == bit, f"Button {name} (0x{bit:04x}) not set correctly"
    
    # Test multiple buttons
    combined = 0x1000 | 0x2000  # A + B
    state = make_state_from_inputs(
        client_id=1, seq=1, buttons=combined,
        lt=0, rt=0, lx=0, ly=0, rx=0, ry=0
    )
    assert state.buttons == combined, "Multiple buttons not set correctly"
    
    print("  ✓ Test passed")


def test_axis_ranges():
    """Test axis value ranges"""
    print("\n=== Test 6: Axis Ranges ===")
    
    # Test stick extremes
    state = make_state_from_inputs(
        client_id=1, seq=1, buttons=0,
        lt=0, rt=0,
        lx=-32768, ly=32767,  # Full left stick range
        rx=-32768, ry=32767   # Full right stick range
    )
    
    data = pack(state)
    decoded = unpack(data)
    
    assert decoded.lx == -32768, "Left stick X min failed"
    assert decoded.ly == 32767, "Left stick Y max failed"
    assert decoded.rx == -32768, "Right stick X min failed"
    assert decoded.ry == 32767, "Right stick Y max failed"
    
    # Test trigger ranges
    state2 = make_state_from_inputs(
        client_id=1, seq=1, buttons=0,
        lt=255, rt=0,
        lx=0, ly=0, rx=0, ry=0
    )
    
    data2 = pack(state2)
    decoded2 = unpack(data2)
    
    assert decoded2.lt == 255, "Left trigger max failed"
    assert decoded2.rt == 0, "Right trigger min failed"
    
    print("  ✓ Test passed")


def test_host_timeout():
    """Test host ownership timeout"""
    print("\n=== Test 7: Host Ownership Timeout ===")
    
    host_msgs = []
    
    def host_cb(msg):
        host_msgs.append(msg)
        if 'timeout' not in msg.lower():
            print(f"  HOST: {msg}")
    
    # Start host
    host = GamepadHost(bind_ip='127.0.0.1', port=17779, status_cb=host_cb)
    host.start()
    time.sleep(0.3)
    
    # Start client and send one packet
    client = GamepadClient(target_ip='127.0.0.1', port=17779, client_id=5000, status_cb=lambda m: None)
    client.start()
    time.sleep(0.2)
    
    # Stop client (host should timeout ownership)
    client.stop()
    time.sleep(1.0)  # Wait for timeout
    
    host.stop()
    time.sleep(0.3)
    
    # Verify timeout occurred
    assert any('owner set' in m for m in host_msgs), "Owner should be set"
    assert any('timeout' in m.lower() for m in host_msgs), "Ownership timeout should occur"
    
    print("  ✓ Test passed - Ownership timeout works")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Cross-Platform Integration Tests")
    print("=" * 60)
    
    tests = [
        test_protocol_encoding,
        test_button_mapping,
        test_axis_ranges,
        test_packet_sequence,
        test_host_client_local,
        test_multiple_clients,
        test_host_timeout,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ Test error: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
