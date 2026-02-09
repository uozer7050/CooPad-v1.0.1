import socket
import threading
import time
from typing import Optional

from .protocol import unpack, PROTOCOL_VERSION
from .security import SecurityManager, SecurityConfig

try:
    import vgamepad as vg
    VGAME_AVAILABLE = True
except Exception:
    VGAME_AVAILABLE = False


class GamepadHost:
    def __init__(self, bind_ip: str = "", port: int = 7777, status_cb=None, telemetry_cb=None, security_config: Optional[SecurityConfig] = None):
        self.bind_ip = bind_ip
        self.port = port
        self._sock: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._last_seq = None
        self._last_buttons = 0
        self._owner = None
        self._last_time = 0.0
        self.status_cb = status_cb or (lambda s: print(f"HOST: {s}"))
        self.telemetry_cb = telemetry_cb or (lambda s: None)
        self._vg = None
        self._packet_count = 0
        self._latency_samples = []
        self._last_telemetry_time = 0
        
        # Initialize security manager
        self._security = SecurityManager(security_config)
        
        # Legacy rate limiting (kept for backward compatibility, but security manager is preferred)
        self._rate_limit_window = 1.0  # seconds
        self._rate_limit_max = 150  # max packets per second per client
        self._client_packet_counts = {}  # client_id -> (timestamp, count)

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
        if self._thread:
            self._thread.join(timeout=1.0)

    def _run(self):
        self.status_cb('listening on %s:%d' % (self.bind_ip or '*', self.port))
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((self.bind_ip, self.port))
        if VGAME_AVAILABLE:
            # Retry vgamepad init up to 3 times – ViGEmBus sometimes needs a
            # moment after system boot or sleep before it accepts connections.
            max_retries = 3
            for attempt in range(1, max_retries + 1):
                try:
                    self._vg = vg.VX360Gamepad()
                    self.status_cb('vgamepad initialized')
                    break
                except Exception as e:
                    self.status_cb(f'vgamepad init attempt {attempt}/{max_retries} failed: {e}')
                    if attempt < max_retries:
                        self.status_cb(f'Retrying in 2 seconds...')
                        # Wait, but honour stop event so we don't block shutdown
                        if self._stop.wait(timeout=2.0):
                            return  # stop was requested during wait
                    else:
                        self.status_cb('⚠ Could not connect to ViGEmBus after all retries.')
                        self.status_cb('→ Try restarting CooPad or reinstalling ViGEmBus driver.')

        while not self._stop.is_set():
            try:
                self._sock.settimeout(0.5)
                data, addr = self._sock.recvfrom(1024)
            except socket.timeout:
                # check ownership timeout
                if self._owner and (time.time() - self._last_time) > 0.5:
                    self.status_cb('owner timeout, clearing state')
                    self._owner = None
                    self._last_seq = None
                continue
            except Exception as e:
                self.status_cb(f'recv error: {e}')
                continue

            try:
                state = unpack(data)
            except Exception as e:
                self.status_cb(f'bad packet: {e}')
                continue

            if state.version != PROTOCOL_VERSION:
                self.status_cb(f'bad version {state.version} from {addr}')
                continue
            
            # Enhanced security check using security manager
            allowed, reason = self._security.check_packet(state.client_id, addr[0], state.timestamp)
            if not allowed:
                # Only log first rejection to avoid spam
                if reason != "IP rate limit exceeded" or self._packet_count % 100 == 0:
                    self.status_cb(f'packet rejected from {addr}: {reason}')
                continue

            # ownership
            if self._owner is None:
                self._owner = state.client_id
                self.status_cb(f'owner set to {self._owner}')

            if state.client_id != self._owner:
                # ignore others
                continue

            # simple seq check
            if self._last_seq is not None:
                diff = (state.sequence - self._last_seq) & 0xFFFF
                if diff == 0:
                    # duplicate
                    continue
            self._last_seq = state.sequence
            self._last_time = time.time()
            self._packet_count += 1

            # Calculate telemetry
            self._update_telemetry(state)

            # apply state to vgamepad if available
            try:
                self._apply_state(state)
            except Exception as e:
                self.status_cb(f'apply state error: {e}')

    def _apply_state(self, state):
        # If no virtual gamepad available, log the state for debugging
        if self._vg is None:
            self.status_cb(f'recv seq={state.sequence} bt={state.buttons:#06x} lt={state.lt} rt={state.rt} lx={state.lx} ly={state.ly} rx={state.rx} ry={state.ry}')
            return

        # Full XInput mapping per protocol.md
        try:
            buttons = state.buttons

            if VGAME_AVAILABLE:
                # mapping: protocol bits -> vgamepad XUSB_BUTTON enum
                mapping = {
                    0x0001: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
                    0x0002: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
                    0x0004: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
                    0x0008: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
                    0x0010: vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
                    0x0020: vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
                    0x0040: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
                    0x0080: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
                    0x0100: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
                    0x0200: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
                    0x1000: vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
                    0x2000: vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
                    0x4000: vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
                    0x8000: vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
                }
            else:
                mapping = {}

            # Press/release based on diff from last_buttons
            for bitmask, btn_enum in mapping.items():
                had = bool(self._last_buttons & bitmask)
                now = bool(buttons & bitmask)
                if now and not had:
                    self._vg.press_button(button=btn_enum)
                elif not now and had:
                    self._vg.release_button(button=btn_enum)

            # update last buttons
            self._last_buttons = buttons

            # axes: both backends expect -32768..32767 for sticks
            lx = int(max(-32768, min(32767, state.lx)))
            ly = int(max(-32768, min(32767, state.ly)))
            rx = int(max(-32768, min(32767, state.rx)))
            ry = int(max(-32768, min(32767, state.ry)))
            self._vg.left_joystick(lx, ly)
            self._vg.right_joystick(rx, ry)

            # triggers 0-255 expected
            lt = int(max(0, min(255, state.lt)))
            rt = int(max(0, min(255, state.rt)))
            self._vg.left_trigger(lt)
            self._vg.right_trigger(rt)

            self._vg.update()
        except Exception as e:
            self.status_cb(f'vgamepad apply error: {e}')
    
    def _update_telemetry(self, state):
        """Calculate and report telemetry metrics."""
        current_time = time.perf_counter()
        
        # Calculate network latency from packet timestamp
        packet_time_ns = state.timestamp
        packet_time_s = packet_time_ns / 1_000_000_000.0
        current_time_ns = time.perf_counter_ns()
        current_time_s = current_time_ns / 1_000_000_000.0
        
        latency_ms = (current_time_s - packet_time_s) * 1000
        
        # Track samples for jitter calculation
        self._latency_samples.append(latency_ms)
        if len(self._latency_samples) > 50:
            self._latency_samples.pop(0)
        
        # Calculate jitter (standard deviation of latency)
        if len(self._latency_samples) >= 2:
            import statistics
            jitter_ms = statistics.stdev(self._latency_samples)
        else:
            jitter_ms = 0.0
        
        # Calculate receive rate
        if not hasattr(self, '_rate_start_time'):
            self._rate_start_time = current_time
            self._rate_packet_count = 0
        
        self._rate_packet_count += 1
        elapsed = current_time - self._rate_start_time
        if elapsed >= 1.0:
            rate_hz = self._rate_packet_count / elapsed
            self._rate_start_time = current_time
            self._rate_packet_count = 0
        else:
            rate_hz = 0
        
        # Report telemetry every second
        if current_time - self._last_telemetry_time >= 1.0:
            if rate_hz > 0:
                self.telemetry_cb(f'Latency: {latency_ms:.1f}ms | Jitter: {jitter_ms:.1f}ms | Rate: {rate_hz:.1f}Hz | seq={state.sequence}')
            else:
                self.telemetry_cb(f'Latency: {latency_ms:.1f}ms | Jitter: {jitter_ms:.1f}ms | seq={state.sequence}')
            self._last_telemetry_time = current_time
    
    def get_security_stats(self) -> dict:
        """Get security statistics from the security manager."""
        return self._security.get_stats()
    
    def get_security_events(self, limit: int = 100) -> list:
        """Get recent security events."""
        return self._security.get_recent_events(limit)
    
    def block_ip(self, ip_address: str, duration: float = None):
        """Manually block an IP address."""
        self._security.block_ip(ip_address, duration)
        self.status_cb(f'IP {ip_address} blocked')
    
    def unblock_ip(self, ip_address: str):
        """Manually unblock an IP address."""
        self._security.unblock_ip(ip_address)
        self.status_cb(f'IP {ip_address} unblocked')
    
    def _check_rate_limit(self, client_id: int, addr) -> bool:
        """
        Legacy rate limiting check (kept for backward compatibility).
        
        NOTE: The SecurityManager provides more comprehensive rate limiting.
        This method is kept for compatibility but should not be used directly.
        """
        current_time = time.time()
        
        # Clean up old entries
        to_remove = []
        for cid, (timestamp, _) in self._client_packet_counts.items():
            if current_time - timestamp > self._rate_limit_window * 2:
                to_remove.append(cid)
        for cid in to_remove:
            del self._client_packet_counts[cid]
        
        # Check/update current client
        if client_id in self._client_packet_counts:
            timestamp, count = self._client_packet_counts[client_id]
            if current_time - timestamp < self._rate_limit_window:
                if count >= self._rate_limit_max:
                    # Rate limit exceeded - log once per window
                    if count == self._rate_limit_max:
                        self.status_cb(f'rate limit exceeded for client {client_id} from {addr}')
                    self._client_packet_counts[client_id] = (timestamp, count + 1)
                    return False
                else:
                    self._client_packet_counts[client_id] = (timestamp, count + 1)
                    return True
            else:
                # New window
                self._client_packet_counts[client_id] = (current_time, 1)
                return True
        else:
            # First packet from this client
            self._client_packet_counts[client_id] = (current_time, 1)
            return True
