"""
Security module for CooPad - DoS protection and connection management.

This module provides comprehensive security features including:
- Enhanced rate limiting with burst protection
- IP-based filtering and blacklisting
- Connection tracking and monitoring
- Timestamp validation for replay attack prevention
- Automatic threat detection and response
"""

import time
import hashlib
from collections import defaultdict
from typing import Dict, Tuple, Set, Optional
from dataclasses import dataclass, field


@dataclass
class SecurityConfig:
    """Configuration for security features."""
    # Rate limiting
    rate_limit_window: float = 1.0  # seconds
    rate_limit_max: int = 120  # max packets per second per client
    rate_limit_burst: int = 20  # max burst packets
    
    # IP-based limits
    ip_rate_limit_max: int = 200  # max packets per second per IP
    max_clients_per_ip: int = 3  # max simultaneous clients from one IP
    
    # Blocking
    auto_block_threshold: int = 5  # violations before auto-block
    block_duration: float = 300.0  # seconds (5 minutes)
    
    # Timestamp validation
    max_timestamp_age: float = 5.0  # seconds
    max_timestamp_future: float = 1.0  # seconds
    
    # Whitelisting
    enable_whitelist: bool = False
    whitelist_ips: Set[str] = field(default_factory=set)
    
    # Security logging
    log_security_events: bool = True
    log_blocked_packets: bool = False


@dataclass
class ClientStats:
    """Statistics for a single client."""
    client_id: int
    ip_address: str
    first_seen: float
    last_seen: float
    packet_count: int = 0
    violations: int = 0
    blocked_until: float = 0.0
    
    def is_blocked(self) -> bool:
        """Check if client is currently blocked."""
        return time.time() < self.blocked_until


class TokenBucket:
    """Token bucket algorithm for rate limiting with burst protection."""
    
    def __init__(self, rate: float, burst: int):
        """
        Initialize token bucket.
        
        Args:
            rate: Tokens per second
            burst: Maximum burst size
        """
        self.rate = rate
        self.burst = burst
        self.tokens = float(burst)
        self.last_update = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were available and consumed, False otherwise
        """
        now = time.time()
        elapsed = now - self.last_update
        self.last_update = now
        
        # Add tokens based on elapsed time
        self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False


class SecurityManager:
    """
    Comprehensive security manager for DoS protection and connection management.
    """
    
    def __init__(self, config: Optional[SecurityConfig] = None):
        """Initialize security manager with configuration."""
        self.config = config or SecurityConfig()
        
        # Client tracking
        self._clients: Dict[int, ClientStats] = {}  # client_id -> stats
        self._ip_clients: Dict[str, Set[int]] = defaultdict(set)  # ip -> set of client_ids
        
        # Rate limiting - per client
        self._client_buckets: Dict[int, TokenBucket] = {}
        
        # Rate limiting - per IP
        self._ip_buckets: Dict[str, TokenBucket] = {}
        self._ip_packet_counts: Dict[str, Tuple[float, int]] = {}  # ip -> (timestamp, count)
        
        # Blocked IPs
        self._blocked_ips: Dict[str, float] = {}  # ip -> blocked_until
        
        # Security event tracking
        self._security_events: list = []
        self._last_cleanup = time.time()
        
    def check_packet(self, client_id: int, ip_address: str, timestamp_ns: int) -> Tuple[bool, str]:
        """
        Check if packet should be accepted.
        
        Args:
            client_id: Client identifier
            ip_address: Source IP address
            timestamp_ns: Packet timestamp in nanoseconds
            
        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        current_time = time.time()
        
        # Periodic cleanup
        if current_time - self._last_cleanup > 60:
            self._cleanup_old_data()
        
        # Check IP whitelist
        if self.config.enable_whitelist:
            if ip_address not in self.config.whitelist_ips:
                self._log_security_event("whitelist_reject", ip_address, client_id)
                return False, "IP not in whitelist"
        
        # Check if IP is blocked
        if ip_address in self._blocked_ips:
            if current_time < self._blocked_ips[ip_address]:
                if self.config.log_blocked_packets:
                    self._log_security_event("blocked_ip", ip_address, client_id)
                return False, "IP is blocked"
            else:
                # Block expired, remove it
                del self._blocked_ips[ip_address]
        
        # Check if client is blocked
        if client_id in self._clients:
            client = self._clients[client_id]
            if client.is_blocked():
                if self.config.log_blocked_packets:
                    self._log_security_event("blocked_client", ip_address, client_id)
                return False, "Client is blocked"
        
        # Validate timestamp to prevent replay attacks
        if not self._validate_timestamp(timestamp_ns):
            self._record_violation(client_id, ip_address, "invalid_timestamp")
            return False, "Invalid timestamp"
        
        # Check IP-based rate limit
        if not self._check_ip_rate_limit(ip_address):
            self._record_violation(client_id, ip_address, "ip_rate_limit")
            return False, "IP rate limit exceeded"
        
        # Check client-based rate limit with burst protection
        if not self._check_client_rate_limit(client_id):
            self._record_violation(client_id, ip_address, "client_rate_limit")
            return False, "Client rate limit exceeded"
        
        # Check max clients per IP
        if not self._check_clients_per_ip(client_id, ip_address):
            self._record_violation(client_id, ip_address, "too_many_clients")
            return False, "Too many clients from IP"
        
        # Update client stats
        self._update_client_stats(client_id, ip_address)
        
        return True, "OK"
    
    def _validate_timestamp(self, timestamp_ns: int) -> bool:
        """Validate packet timestamp to prevent replay attacks."""
        current_time_ns = time.perf_counter_ns()
        packet_age_s = (current_time_ns - timestamp_ns) / 1_000_000_000.0
        
        # Check if timestamp is too old
        if packet_age_s > self.config.max_timestamp_age:
            return False
        
        # Check if timestamp is too far in the future
        if packet_age_s < -self.config.max_timestamp_future:
            return False
        
        return True
    
    def _check_ip_rate_limit(self, ip_address: str) -> bool:
        """Check IP-based rate limit."""
        # Get or create token bucket for this IP
        if ip_address not in self._ip_buckets:
            self._ip_buckets[ip_address] = TokenBucket(
                rate=self.config.ip_rate_limit_max,
                burst=self.config.rate_limit_burst
            )
        
        return self._ip_buckets[ip_address].consume(1)
    
    def _check_client_rate_limit(self, client_id: int) -> bool:
        """Check client-based rate limit with burst protection."""
        # Get or create token bucket for this client
        if client_id not in self._client_buckets:
            self._client_buckets[client_id] = TokenBucket(
                rate=self.config.rate_limit_max,
                burst=self.config.rate_limit_burst
            )
        
        return self._client_buckets[client_id].consume(1)
    
    def _check_clients_per_ip(self, client_id: int, ip_address: str) -> bool:
        """Check if IP has too many simultaneous clients."""
        clients = self._ip_clients[ip_address]
        
        # If client already known from this IP, allow it
        if client_id in clients:
            return True
        
        # Check if IP has reached max clients
        if len(clients) >= self.config.max_clients_per_ip:
            return False
        
        # Add client to IP's client set
        clients.add(client_id)
        return True
    
    def _update_client_stats(self, client_id: int, ip_address: str):
        """Update statistics for a client."""
        current_time = time.time()
        
        if client_id not in self._clients:
            self._clients[client_id] = ClientStats(
                client_id=client_id,
                ip_address=ip_address,
                first_seen=current_time,
                last_seen=current_time,
                packet_count=1
            )
        else:
            client = self._clients[client_id]
            client.last_seen = current_time
            client.packet_count += 1
    
    def _record_violation(self, client_id: int, ip_address: str, reason: str):
        """Record a security violation and take action if necessary."""
        current_time = time.time()
        
        # Update client violation count
        if client_id in self._clients:
            client = self._clients[client_id]
            client.violations += 1
            
            # Auto-block if threshold reached
            if client.violations >= self.config.auto_block_threshold:
                client.blocked_until = current_time + self.config.block_duration
                self._log_security_event("auto_block_client", ip_address, client_id, reason)
        
        # Track IP violations
        if ip_address not in self._ip_clients:
            self._ip_clients[ip_address] = set()
        
        # Log security event
        self._log_security_event("violation", ip_address, client_id, reason)
    
    def _log_security_event(self, event_type: str, ip_address: str, client_id: int, detail: str = ""):
        """Log a security event."""
        if not self.config.log_security_events:
            return
        
        event = {
            'timestamp': time.time(),
            'type': event_type,
            'ip': ip_address,
            'client_id': client_id,
            'detail': detail
        }
        self._security_events.append(event)
        
        # Keep only recent events (last 1000)
        if len(self._security_events) > 1000:
            self._security_events = self._security_events[-1000:]
    
    def _cleanup_old_data(self):
        """Clean up old tracking data to prevent memory leaks."""
        current_time = time.time()
        self._last_cleanup = current_time
        
        # Remove expired blocks
        expired_blocks = [ip for ip, until in self._blocked_ips.items() if current_time >= until]
        for ip in expired_blocks:
            del self._blocked_ips[ip]
        
        # Remove inactive clients (not seen in 5 minutes)
        inactive_threshold = current_time - 300
        inactive_clients = [
            cid for cid, stats in self._clients.items()
            if stats.last_seen < inactive_threshold and not stats.is_blocked()
        ]
        for cid in inactive_clients:
            client = self._clients[cid]
            # Remove from IP tracking
            if client.ip_address in self._ip_clients:
                self._ip_clients[client.ip_address].discard(cid)
            del self._clients[cid]
            if cid in self._client_buckets:
                del self._client_buckets[cid]
        
        # Remove empty IP client sets
        empty_ips = [ip for ip, clients in self._ip_clients.items() if len(clients) == 0]
        for ip in empty_ips:
            del self._ip_clients[ip]
            if ip in self._ip_buckets:
                del self._ip_buckets[ip]
    
    def block_ip(self, ip_address: str, duration: float = None):
        """Manually block an IP address."""
        if duration is None:
            duration = self.config.block_duration
        self._blocked_ips[ip_address] = time.time() + duration
        self._log_security_event("manual_block", ip_address, 0, f"duration={duration}s")
    
    def unblock_ip(self, ip_address: str):
        """Manually unblock an IP address."""
        if ip_address in self._blocked_ips:
            del self._blocked_ips[ip_address]
            self._log_security_event("manual_unblock", ip_address, 0)
    
    def get_stats(self) -> dict:
        """Get security statistics."""
        current_time = time.time()
        
        active_clients = sum(1 for c in self._clients.values() if current_time - c.last_seen < 60)
        blocked_clients = sum(1 for c in self._clients.values() if c.is_blocked())
        blocked_ips = len([ip for ip, until in self._blocked_ips.items() if current_time < until])
        
        return {
            'total_clients': len(self._clients),
            'active_clients': active_clients,
            'blocked_clients': blocked_clients,
            'blocked_ips': blocked_ips,
            'tracked_ips': len(self._ip_clients),
            'recent_events': len(self._security_events),
        }
    
    def get_recent_events(self, limit: int = 100) -> list:
        """Get recent security events."""
        return self._security_events[-limit:]
