# CooPad Security Documentation

## Overview

CooPad implements comprehensive security measures to protect against various attacks, particularly Denial of Service (DoS) attacks. This document outlines the security features, best practices, and configuration options.

## Table of Contents

1. [Current Security Features](#current-security-features)
2. [DoS Protection](#dos-protection)
3. [Security Configuration](#security-configuration)
4. [Best Practices](#best-practices)
5. [Monitoring and Incident Response](#monitoring-and-incident-response)
6. [Known Limitations](#known-limitations)
7. [Roadmap](#roadmap)

## Current Security Features

### 1. Multi-Layer Rate Limiting

CooPad implements sophisticated rate limiting at multiple levels:

#### Client-Based Rate Limiting
- **Token Bucket Algorithm**: Prevents burst attacks while allowing normal traffic
- **Default Limits**: 120 packets/second with burst capacity of 20 packets
- **Per-Client Tracking**: Each client_id is tracked independently
- **Automatic Cleanup**: Inactive clients are automatically removed

#### IP-Based Rate Limiting
- **IP-Level Protection**: Limits total packets from a single IP address
- **Default Limit**: 200 packets/second per IP
- **Multiple Clients**: Supports up to 3 simultaneous clients per IP by default
- **Cross-Client Protection**: Prevents one malicious client from affecting others on same IP

### 2. Packet Validation

#### Protocol Validation
- **Version Checking**: Only accepts packets with correct protocol version (v2)
- **Size Validation**: Rejects oversized packets (> 1024 bytes) and undersized packets
- **Value Range Validation**:
  - Buttons: 0-0xFFFF (16-bit)
  - Triggers: 0-255 (8-bit)
  - Joysticks: -32768 to 32767 (16-bit signed)
  - Sequence: 0-0xFFFF (16-bit)

#### Timestamp Validation
- **Replay Attack Prevention**: Rejects packets with old timestamps
- **Age Limit**: Packets older than 5 seconds are rejected
- **Future Timestamp Check**: Rejects packets with timestamps too far in future (>1 second)
- **High-Precision Timing**: Uses nanosecond timestamps for accuracy

### 3. Connection Management

#### Ownership Model
- **Single Owner**: Only one client can control the gamepad at a time
- **First-Come-First-Served**: First client to connect becomes owner
- **Timeout Protection**: Owner is cleared after 0.5 seconds of inactivity
- **Graceful Handover**: Allows new clients to take over if owner disconnects

#### Duplicate Detection
- **Sequence Number Tracking**: Detects and drops duplicate packets
- **16-bit Sequence**: Wraps around automatically (0-65535)
- **Prevents Replay**: Combined with timestamp validation for robust protection

### 4. Automatic Threat Response

#### Violation Tracking
- **Per-Client Violations**: Tracks security violations for each client
- **Auto-Blocking**: Automatically blocks clients after 5 violations
- **Block Duration**: Default 5-minute block duration
- **Progressive Response**: Warnings before permanent blocks

#### IP Blocking
- **Manual Blocking**: Administrators can manually block IPs
- **Automatic Unblocking**: Blocks expire automatically
- **Whitelist Support**: Optional IP whitelist for trusted sources
- **Persistent Tracking**: Blocked IPs remain blocked even if client_id changes

### 5. Security Logging

#### Event Tracking
- **Comprehensive Logging**: Logs all security events
- **Recent Events Buffer**: Keeps last 1000 security events in memory
- **Event Types**:
  - `violation`: Rate limit or validation failures
  - `auto_block_client`: Automatic client blocking
  - `manual_block`/`manual_unblock`: Manual IP blocks
  - `whitelist_reject`: Packets from non-whitelisted IPs
  - `blocked_ip`/`blocked_client`: Blocked packet attempts

#### Configurable Logging
- **Security Events**: Can be enabled/disabled
- **Blocked Packets**: Option to log every blocked packet (can be verbose)
- **Performance**: Minimal performance impact when logging disabled

## DoS Protection

### Attack Vectors and Mitigations

#### 1. Flood Attacks
**Attack**: Overwhelming the host with high packet rates

**Mitigations**:
- Token bucket rate limiting with burst protection
- IP-based rate limiting (200 packets/second per IP)
- Client-based rate limiting (120 packets/second per client)
- Automatic blocking of repeat offenders

#### 2. Amplification Attacks
**Attack**: Sending small packets to trigger large responses

**Mitigations**:
- No response packets sent to clients (one-way UDP)
- Minimal processing for invalid packets
- Early rejection at validation stage

#### 3. Resource Exhaustion
**Attack**: Consuming memory or CPU resources

**Mitigations**:
- Automatic cleanup of inactive connections
- Limited tracking data per client
- Efficient data structures (token buckets, hash maps)
- Periodic cleanup every 60 seconds
- Maximum 1000 security events retained

#### 4. Replay Attacks
**Attack**: Resending captured valid packets

**Mitigations**:
- Timestamp validation (max 5 seconds old)
- Sequence number tracking
- Duplicate packet detection
- High-precision timing (nanosecond)

#### 5. Client ID Spoofing
**Attack**: Pretending to be another client

**Mitigations**:
- IP address tracking for each client_id
- Maximum clients per IP limit
- Ownership model prevents control theft
- Violation tracking per client_id

## Security Configuration

### Basic Configuration

```python
from gp.core.security import SecurityConfig
from gp.core.host import GamepadHost

# Create custom security configuration
config = SecurityConfig(
    # Rate limiting
    rate_limit_max=120,          # packets per second per client
    rate_limit_burst=20,         # maximum burst size
    ip_rate_limit_max=200,       # packets per second per IP
    
    # Connection limits
    max_clients_per_ip=3,        # simultaneous clients per IP
    
    # Blocking
    auto_block_threshold=5,      # violations before auto-block
    block_duration=300.0,        # block duration in seconds
    
    # Timestamp validation
    max_timestamp_age=5.0,       # maximum packet age in seconds
    max_timestamp_future=1.0,    # maximum future timestamp in seconds
    
    # Logging
    log_security_events=True,    # enable security event logging
    log_blocked_packets=False    # log every blocked packet (verbose)
)

# Create host with custom security configuration
host = GamepadHost(
    bind_ip="",
    port=7777,
    security_config=config
)
```

### Whitelist Configuration

For maximum security in trusted environments:

```python
config = SecurityConfig(
    enable_whitelist=True,
    whitelist_ips={'192.168.1.100', '192.168.1.101', '10.0.0.50'}
)
```

### Strict Configuration (High Security)

For public or untrusted networks:

```python
config = SecurityConfig(
    rate_limit_max=60,              # Lower rate limit
    rate_limit_burst=10,            # Smaller burst
    ip_rate_limit_max=100,          # Stricter IP limit
    max_clients_per_ip=1,           # One client per IP
    auto_block_threshold=3,         # Block faster
    block_duration=600.0,           # Longer blocks (10 minutes)
    max_timestamp_age=2.0,          # Tighter timestamp window
    log_blocked_packets=True        # Log everything
)
```

### Relaxed Configuration (Private LAN)

For trusted local networks:

```python
config = SecurityConfig(
    rate_limit_max=180,             # Higher rate limit
    rate_limit_burst=30,            # Larger burst for responsiveness
    ip_rate_limit_max=300,          # Relaxed IP limit
    max_clients_per_ip=5,           # Multiple clients per IP
    auto_block_threshold=10,        # More tolerant
    block_duration=120.0,           # Shorter blocks (2 minutes)
    max_timestamp_age=10.0,         # Wider timestamp window
    log_security_events=True,
    log_blocked_packets=False
)
```

## Best Practices

### Network Security

1. **Firewall Configuration**
   - Only open UDP port 7777 (or your chosen port)
   - Limit access to specific IP ranges if possible
   - Use network-level rate limiting if available

2. **Network Isolation**
   - Run CooPad on an isolated network segment if possible
   - Use VPN for remote connections (ZeroTier, Tailscale, WireGuard)
   - Avoid exposing directly to the internet

3. **VPN Recommendations**
   - **ZeroTier**: Easy setup, good for home use
   - **Tailscale**: Excellent security, WireGuard-based
   - **OpenVPN**: Industry standard, requires more setup
   - **WireGuard**: Modern, fast, secure

### Deployment Security

1. **Host Machine**
   - Keep operating system updated
   - Use minimal services on the host machine
   - Enable host firewall
   - Regularly monitor logs

2. **Client Machine**
   - Authenticate client machine before granting access
   - Use secure client_id generation
   - Monitor for unusual behavior

3. **Monitoring**
   ```python
   # Periodically check security stats
   stats = host.get_security_stats()
   print(f"Active clients: {stats['active_clients']}")
   print(f"Blocked clients: {stats['blocked_clients']}")
   print(f"Blocked IPs: {stats['blocked_ips']}")
   
   # Review security events
   events = host.get_security_events(limit=50)
   for event in events:
       if event['type'] in ['auto_block_client', 'violation']:
           print(f"Security event: {event}")
   ```

### Application Security

1. **Regular Updates**
   - Keep CooPad updated to latest version
   - Monitor security advisories
   - Apply patches promptly

2. **Configuration Management**
   - Store security configuration securely
   - Don't commit sensitive data to version control
   - Use environment variables for sensitive settings

3. **Incident Response**
   - Have a plan for handling security incidents
   - Monitor logs regularly
   - Know how to block malicious IPs quickly:
     ```python
     host.block_ip('192.168.1.100', duration=3600)  # Block for 1 hour
     ```

## Monitoring and Incident Response

### Real-Time Monitoring

```python
# Get comprehensive security statistics
stats = host.get_security_stats()
print(f"""
Security Status:
- Total clients tracked: {stats['total_clients']}
- Currently active: {stats['active_clients']}
- Blocked clients: {stats['blocked_clients']}
- Blocked IP addresses: {stats['blocked_ips']}
- Tracked IP addresses: {stats['tracked_ips']}
- Recent security events: {stats['recent_events']}
""")
```

### Event Analysis

```python
# Analyze recent security events
events = host.get_security_events(limit=100)

# Count event types
event_counts = {}
for event in events:
    event_type = event['type']
    event_counts[event_type] = event_counts.get(event_type, 0) + 1

print("Event summary:")
for event_type, count in sorted(event_counts.items()):
    print(f"  {event_type}: {count}")

# Find most problematic IPs
ip_violations = {}
for event in events:
    if event['type'] == 'violation':
        ip = event['ip']
        ip_violations[ip] = ip_violations.get(ip, 0) + 1

print("\nMost violations by IP:")
for ip, count in sorted(ip_violations.items(), key=lambda x: x[1], reverse=True)[:5]:
    print(f"  {ip}: {count} violations")
```

### Incident Response Procedures

1. **Detecting an Attack**
   - Sudden increase in blocked packets
   - Many violations from same IP or client
   - High rate of auto-blocks
   - Performance degradation

2. **Immediate Response**
   ```python
   # Block the attacking IP immediately
   host.block_ip('malicious.ip.address', duration=3600)
   
   # Get details about the attack
   events = host.get_security_events(limit=500)
   attack_events = [e for e in events if e['ip'] == 'malicious.ip.address']
   
   # Review and document
   for event in attack_events[-10:]:
       print(f"{event['timestamp']}: {event['type']} - {event['detail']}")
   ```

3. **Post-Incident**
   - Review logs to understand attack pattern
   - Adjust security configuration if needed
   - Consider adding to permanent blocklist
   - Document incident for future reference

### Automated Monitoring Script

```python
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('security_monitor')

def monitor_security(host, check_interval=60):
    """Continuously monitor security status."""
    last_stats = None
    
    while True:
        stats = host.get_security_stats()
        
        # Alert on new blocks
        if last_stats:
            new_blocked_clients = stats['blocked_clients'] - last_stats['blocked_clients']
            new_blocked_ips = stats['blocked_ips'] - last_stats['blocked_ips']
            
            if new_blocked_clients > 0:
                logger.warning(f"NEW: {new_blocked_clients} clients blocked")
            if new_blocked_ips > 0:
                logger.warning(f"NEW: {new_blocked_ips} IPs blocked")
        
        # Alert on high violation rate
        events = host.get_security_events(limit=100)
        recent_violations = [e for e in events if e['type'] == 'violation' and time.time() - e['timestamp'] < 60]
        
        if len(recent_violations) > 20:
            logger.warning(f"HIGH VIOLATION RATE: {len(recent_violations)} violations in last minute")
        
        last_stats = stats
        time.sleep(check_interval)

# Start monitoring in background thread
import threading
monitor_thread = threading.Thread(target=monitor_security, args=(host,), daemon=True)
monitor_thread.start()
```

## Known Limitations

1. **UDP Protocol**: No built-in encryption or authentication at transport layer
   - **Mitigation**: Use VPN for secure tunneling
   - **Future**: Consider DTLS implementation

2. **No Persistent Blocklist**: Blocked IPs reset on application restart
   - **Mitigation**: Implement firewall rules for persistent blocks
   - **Future**: Add persistent blocklist file

3. **Client ID Spoofing**: Client IDs can be spoofed if IP matches
   - **Mitigation**: Use IP whitelist in trusted environments
   - **Future**: Add authentication tokens

4. **Memory-Based Tracking**: All tracking data stored in memory
   - **Mitigation**: Automatic cleanup prevents unbounded growth
   - **Future**: Optional persistent storage for large deployments

5. **No Distributed DoS Protection**: Single host handles all protection
   - **Mitigation**: Deploy behind load balancer with DDoS protection
   - **Future**: Implement distributed rate limiting

## Roadmap

### Short-term (Next Release)
- [ ] Persistent blocklist file
- [ ] Enhanced logging with file output
- [ ] Web dashboard for security monitoring
- [ ] Configurable alert thresholds

### Medium-term
- [ ] Authentication tokens
- [ ] Certificate-based client authentication
- [ ] Integration with external threat intelligence
- [ ] Geographic IP blocking
- [ ] Advanced anomaly detection

### Long-term
- [ ] DTLS encryption support
- [ ] Distributed rate limiting
- [ ] Cloud-based security service
- [ ] Machine learning threat detection
- [ ] Integration with SIEM systems

## Support and Reporting

### Security Issues
If you discover a security vulnerability, please report it privately:
- **Email**: [Create issue on GitHub with "Security" label]
- **Response Time**: We aim to respond within 48 hours
- **Disclosure**: Coordinated disclosure after patch is available

### Questions and Discussions
- GitHub Issues: For feature requests and bug reports
- GitHub Discussions: For general security questions
- Documentation: Refer to README.md for setup instructions

## License
This security documentation is part of CooPad and is provided under the same license as the main project.

---

**Last Updated**: 2026-02-01  
**Version**: 5.1  
**Security Module Version**: 1.0
