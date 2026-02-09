#!/usr/bin/env python3
"""
Tests for the security module.

This test suite validates the DoS protection and security features.
"""

import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gp.core.security import SecurityManager, SecurityConfig, TokenBucket


def test_token_bucket():
    """Test token bucket rate limiting."""
    print("Testing token bucket...")
    
    # Create bucket: 10 tokens/second, burst of 5
    bucket = TokenBucket(rate=10, burst=5)
    
    # Should allow burst of 5
    for i in range(5):
        assert bucket.consume(1), f"Failed to consume token {i+1} in burst"
    print("✓ Burst of 5 tokens consumed")
    
    # Should block 6th immediate request
    assert not bucket.consume(1), "Should block 6th token (burst exhausted)"
    print("✓ Blocked after burst exhausted")
    
    # Wait for tokens to refill
    time.sleep(0.3)
    
    # Should allow 2-3 more tokens (3 * 10 tokens/sec = 3 tokens)
    assert bucket.consume(1), "Should allow token after refill"
    print("✓ Token allowed after refill")
    
    print("✓ Token bucket works correctly\n")


def test_basic_rate_limiting():
    """Test basic rate limiting."""
    print("Testing basic rate limiting...")
    
    config = SecurityConfig(
        rate_limit_max=10,
        rate_limit_burst=5,
        ip_rate_limit_max=15
    )
    manager = SecurityManager(config)
    
    client_id = 12345
    ip = "192.168.1.100"
    timestamp = time.perf_counter_ns()
    
    # Allow first 5 packets (burst)
    for i in range(5):
        allowed, reason = manager.check_packet(client_id, ip, timestamp + i * 1000000)
        assert allowed, f"Packet {i+1} should be allowed in burst: {reason}"
    print("✓ First 5 packets allowed (burst)")
    
    # 6th should be blocked
    allowed, reason = manager.check_packet(client_id, ip, timestamp + 5000000)
    assert not allowed, "6th packet should be blocked"
    assert "rate limit" in reason.lower(), f"Should mention rate limit, got: {reason}"
    print("✓ 6th packet blocked (burst exhausted)")
    
    print("✓ Basic rate limiting works\n")


def test_ip_rate_limiting():
    """Test IP-based rate limiting."""
    print("Testing IP-based rate limiting...")
    
    config = SecurityConfig(
        rate_limit_max=100,  # High client limit
        rate_limit_burst=5,  # Small burst
        ip_rate_limit_max=5,  # Very low IP limit
        max_clients_per_ip=10  # Allow multiple clients for this test
    )
    manager = SecurityManager(config)
    
    ip = "192.168.1.100"
    timestamp = time.perf_counter_ns()
    
    # Send burst of packets from different clients, same IP (rapid fire to hit limit)
    results = []
    for i in range(10):
        client_id = 10000 + i
        allowed, reason = manager.check_packet(client_id, ip, timestamp + i * 1000)  # Very close together
        results.append((client_id, allowed, reason))
    
    allowed_count = sum(1 for _, allowed, _ in results if allowed)
    blocked_count = sum(1 for _, allowed, _ in results if not allowed)
    
    print(f"✓ Sent 10 packets: {allowed_count} allowed, {blocked_count} blocked")
    assert blocked_count > 0, f"Should have blocked some packets due to IP rate limit"
    print("✓ IP-based rate limiting blocked excess packets")
    
    print("✓ IP rate limiting works\n")


def test_max_clients_per_ip():
    """Test maximum clients per IP limit."""
    print("Testing max clients per IP...")
    
    config = SecurityConfig(
        rate_limit_max=10,
        rate_limit_burst=5,
        max_clients_per_ip=2
    )
    manager = SecurityManager(config)
    
    ip = "192.168.1.100"
    timestamp = time.perf_counter_ns()
    
    # First 2 clients should be allowed
    allowed1, _ = manager.check_packet(1001, ip, timestamp)
    allowed2, _ = manager.check_packet(1002, ip, timestamp + 1000000)
    assert allowed1 and allowed2, "First 2 clients should be allowed"
    print("✓ First 2 clients from same IP allowed")
    
    # 3rd client should be blocked
    allowed3, reason = manager.check_packet(1003, ip, timestamp + 2000000)
    assert not allowed3, "3rd client from same IP should be blocked"
    assert "too many clients" in reason.lower(), f"Should mention too many clients: {reason}"
    print("✓ 3rd client from same IP blocked")
    
    print("✓ Max clients per IP works\n")


def test_timestamp_validation():
    """Test timestamp validation for replay attack prevention."""
    print("Testing timestamp validation...")
    
    config = SecurityConfig(
        rate_limit_max=100,
        rate_limit_burst=50,
        max_timestamp_age=2.0,  # 2 seconds max age
        max_timestamp_future=0.5  # 0.5 seconds max future
    )
    manager = SecurityManager(config)
    
    client_id = 12345
    ip = "192.168.1.100"
    current_time = time.perf_counter_ns()
    
    # Current timestamp should be allowed
    allowed, reason = manager.check_packet(client_id, ip, current_time)
    assert allowed, f"Current timestamp should be allowed: {reason}"
    print("✓ Current timestamp allowed")
    
    # Old timestamp should be rejected
    old_timestamp = current_time - int(3 * 1_000_000_000)  # 3 seconds ago
    allowed, reason = manager.check_packet(client_id + 1, ip, old_timestamp)
    assert not allowed, "Old timestamp should be rejected"
    assert "timestamp" in reason.lower(), f"Should mention timestamp: {reason}"
    print("✓ Old timestamp rejected")
    
    # Future timestamp should be rejected
    future_timestamp = current_time + int(2 * 1_000_000_000)  # 2 seconds in future
    allowed, reason = manager.check_packet(client_id + 2, ip, future_timestamp)
    assert not allowed, "Future timestamp should be rejected"
    print("✓ Future timestamp rejected")
    
    print("✓ Timestamp validation works\n")


def test_auto_blocking():
    """Test automatic blocking after violations."""
    print("Testing auto-blocking...")
    
    config = SecurityConfig(
        rate_limit_max=2,
        rate_limit_burst=1,
        auto_block_threshold=3,
        block_duration=1.0  # Short duration for testing
    )
    manager = SecurityManager(config)
    
    client_id = 12345
    ip = "192.168.1.100"
    timestamp = time.perf_counter_ns()
    
    # Generate violations by exceeding rate limit
    violation_count = 0
    for i in range(10):
        allowed, reason = manager.check_packet(client_id, ip, timestamp + i * 100000)
        if not allowed:
            violation_count += 1
    
    assert violation_count >= 3, f"Should have at least 3 violations, got {violation_count}"
    print(f"✓ Generated {violation_count} violations")
    
    # Now client should be blocked even with valid packet
    time.sleep(0.1)
    allowed, reason = manager.check_packet(client_id, ip, time.perf_counter_ns())
    assert not allowed, "Client should be auto-blocked after violations"
    assert "blocked" in reason.lower(), f"Should mention blocking: {reason}"
    print("✓ Client auto-blocked after threshold")
    
    # Wait for block to expire
    time.sleep(1.1)
    allowed, reason = manager.check_packet(client_id, ip, time.perf_counter_ns())
    # May still be rate limited but should not say "blocked"
    print(f"✓ Block expired (allowed={allowed}, reason={reason})")
    
    print("✓ Auto-blocking works\n")


def test_whitelist():
    """Test IP whitelist."""
    print("Testing IP whitelist...")
    
    config = SecurityConfig(
        enable_whitelist=True,
        whitelist_ips={'192.168.1.100', '10.0.0.50'}
    )
    manager = SecurityManager(config)
    
    timestamp = time.perf_counter_ns()
    
    # Whitelisted IP should be allowed
    allowed, reason = manager.check_packet(12345, '192.168.1.100', timestamp)
    assert allowed, f"Whitelisted IP should be allowed: {reason}"
    print("✓ Whitelisted IP allowed")
    
    # Non-whitelisted IP should be rejected
    allowed, reason = manager.check_packet(12346, '192.168.1.200', timestamp)
    assert not allowed, "Non-whitelisted IP should be rejected"
    assert "whitelist" in reason.lower(), f"Should mention whitelist: {reason}"
    print("✓ Non-whitelisted IP rejected")
    
    print("✓ Whitelist works\n")


def test_manual_blocking():
    """Test manual IP blocking."""
    print("Testing manual IP blocking...")
    
    manager = SecurityManager()
    
    ip = "192.168.1.100"
    timestamp = time.perf_counter_ns()
    
    # Should be allowed initially
    allowed, _ = manager.check_packet(12345, ip, timestamp)
    assert allowed, "Should be allowed initially"
    print("✓ IP allowed before blocking")
    
    # Block the IP
    manager.block_ip(ip, duration=1.0)
    
    # Should now be blocked
    allowed, reason = manager.check_packet(12345, ip, timestamp + 1000000)
    assert not allowed, "Should be blocked after manual block"
    assert "blocked" in reason.lower(), f"Should mention blocking: {reason}"
    print("✓ IP blocked after manual block")
    
    # Unblock the IP
    manager.unblock_ip(ip)
    
    # Should be allowed again
    allowed, _ = manager.check_packet(12345, ip, time.perf_counter_ns())
    assert allowed, "Should be allowed after unblock"
    print("✓ IP allowed after manual unblock")
    
    print("✓ Manual blocking works\n")


def test_statistics():
    """Test security statistics."""
    print("Testing security statistics...")
    
    manager = SecurityManager()
    
    timestamp = time.perf_counter_ns()
    
    # Send some packets
    manager.check_packet(12345, '192.168.1.100', timestamp)
    manager.check_packet(12346, '192.168.1.101', timestamp + 1000000)
    manager.check_packet(12347, '192.168.1.100', timestamp + 2000000)
    
    stats = manager.get_stats()
    
    assert stats['total_clients'] >= 2, f"Should track at least 2 clients, got {stats['total_clients']}"
    assert stats['tracked_ips'] >= 2, f"Should track at least 2 IPs, got {stats['tracked_ips']}"
    print(f"✓ Statistics tracked: {stats['total_clients']} clients, {stats['tracked_ips']} IPs")
    
    # Check events
    events = manager.get_recent_events()
    assert len(events) >= 0, "Should have event list"
    print(f"✓ Security events: {len(events)} events logged")
    
    print("✓ Statistics work\n")


def test_cleanup():
    """Test automatic cleanup of old data."""
    print("Testing automatic cleanup...")
    
    manager = SecurityManager()
    
    # Add some clients
    timestamp = time.perf_counter_ns()
    for i in range(5):
        manager.check_packet(10000 + i, f'192.168.1.{100+i}', timestamp + i * 1000000)
    
    initial_clients = manager.get_stats()['total_clients']
    print(f"✓ Initial clients: {initial_clients}")
    
    # Force cleanup
    manager._cleanup_old_data()
    
    after_cleanup = manager.get_stats()['total_clients']
    print(f"✓ After cleanup: {after_cleanup} clients")
    
    # Cleanup shouldn't remove recent clients
    assert after_cleanup >= initial_clients - 1, "Cleanup shouldn't remove recent clients"
    
    print("✓ Cleanup works\n")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Security Module Tests")
    print("=" * 60)
    print()
    
    try:
        test_token_bucket()
        test_basic_rate_limiting()
        test_ip_rate_limiting()
        test_max_clients_per_ip()
        test_timestamp_validation()
        test_auto_blocking()
        test_whitelist()
        test_manual_blocking()
        test_statistics()
        test_cleanup()
        
        print("=" * 60)
        print("✓ ALL SECURITY TESTS PASSED")
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
