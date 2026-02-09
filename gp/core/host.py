import socket
import threading
import time
import random
from typing import Optional, Dict, Any

from .protocol import unpack, PROTOCOL_VERSION
from .security import SecurityManager, SecurityConfig

try:
    import vgamepad as vg
    VGAME_AVAILABLE = True
except Exception:
    VGAME_AVAILABLE = False

# Random name pools for connected clients
_ADJECTIVES = [
    'Swift', 'Brave', 'Crimson', 'Neon', 'Shadow', 'Cosmic', 'Thunder',
    'Frozen', 'Blazing', 'Silent', 'Iron', 'Golden', 'Pixel', 'Turbo',
    'Phantom', 'Mystic', 'Radiant', 'Storm', 'Ember', 'Cobalt',
]
_NOUNS = [
    'Falcon', 'Wolf', 'Titan', 'Phoenix', 'Viper', 'Dragon', 'Knight',
    'Hawk', 'Panther', 'Fox', 'Bear', 'Raven', 'Lynx', 'Shark',
    'Eagle', 'Lion', 'Cobra', 'Jaguar', 'Orca', 'Rex',
]
_COLORS = [
    '#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6',
    '#1abc9c', '#e67e22', '#00bcd4', '#ff6b81', '#a29bfe',
    '#fd79a8', '#00cec9', '#ffeaa7', '#74b9ff', '#55efc4',
]


def _generate_player_name() -> str:
    return f"{random.choice(_ADJECTIVES)} {random.choice(_NOUNS)}"


def _generate_player_color() -> str:
    return random.choice(_COLORS)


MAX_CONTROLLERS = 4  # XInput hardware limit


class GamepadHost:
    def __init__(self, bind_ip: str = "", port: int = 7777, status_cb=None, telemetry_cb=None,
                 security_config: Optional[SecurityConfig] = None, multi_gamepad: bool = False):
        self.bind_ip = bind_ip
        self.port = port
        self._sock: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self.status_cb = status_cb or (lambda s: print(f"HOST: {s}"))
        self.telemetry_cb = telemetry_cb or (lambda s: None)
        self._packet_count = 0
        self._last_telemetry_time = 0

        # Multi-gamepad mode
        self.multi_gamepad = multi_gamepad

        # --- Single-controller (legacy) state ---
        self._owner = None
        self._last_seq_single = None
        self._last_buttons_single = 0
        self._last_time_single = 0.0
        self._vg_single = None
        self._latency_samples_single: list = []

        # --- Multi-controller state ---
        # client_id -> {gamepad, last_seq, last_buttons, last_time, name, color, latency_samples, ...}
        self._clients: Dict[int, Dict[str, Any]] = {}
        self._client_slot_order: list = []  # ordered list of client_ids for slot numbering

        # Initialize security manager
        self._security = SecurityManager(security_config)

        # Legacy rate limiting (kept for backward compatibility)
        self._rate_limit_window = 1.0
        self._rate_limit_max = 300
        self._client_packet_counts = {}

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

    def _init_single_gamepad(self):
        """Initialize a single virtual gamepad (legacy mode)."""
        if not VGAME_AVAILABLE:
            return
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                self._vg_single = vg.VX360Gamepad()
                self.status_cb('vgamepad initialized (single mode)')
                return
            except Exception as e:
                self.status_cb(f'vgamepad init attempt {attempt}/{max_retries} failed: {e}')
                if attempt < max_retries:
                    self.status_cb('Retrying in 2 seconds...')
                    if self._stop.wait(timeout=2.0):
                        return
                else:
                    self.status_cb('⚠ Could not connect to ViGEmBus after all retries.')
                    self.status_cb('→ Try restarting CooPad or reinstalling ViGEmBus driver.')

    def _get_or_create_gamepad(self, client_id: int):
        """Get existing or create new virtual gamepad for a client (multi mode)."""
        if client_id in self._clients:
            return self._clients[client_id]['gamepad']
        if len(self._clients) >= MAX_CONTROLLERS:
            self.status_cb(f'max controllers ({MAX_CONTROLLERS}) reached, rejecting client {client_id}')
            return None
        if not VGAME_AVAILABLE:
            # Create entry without real gamepad
            name = _generate_player_name()
            color = _generate_player_color()
            slot = len(self._clients) + 1
            self._clients[client_id] = {
                'gamepad': None,
                'last_seq': None,
                'last_buttons': 0,
                'last_time': time.time(),
                'name': name,
                'color': color,
                'slot': slot,
                'latency_samples': [],
                'last_telemetry_time': 0,
                'rate_start_time': time.perf_counter(),
                'rate_packet_count': 0,
                'addr': None,
            }
            self._client_slot_order.append(client_id)
            self.status_cb(f'[Player {slot}] "{name}" connected (no vgamepad driver)')
            self.telemetry_cb(f'PLAYER_JOIN|{client_id}|{name}|{color}|{slot}')
            return None
        try:
            gp = vg.VX360Gamepad()
        except Exception as e:
            self.status_cb(f'failed to create gamepad for client {client_id}: {e}')
            return None
        name = _generate_player_name()
        color = _generate_player_color()
        slot = len(self._clients) + 1
        self._clients[client_id] = {
            'gamepad': gp,
            'last_seq': None,
            'last_buttons': 0,
            'last_time': time.time(),
            'name': name,
            'color': color,
            'slot': slot,
            'latency_samples': [],
            'last_telemetry_time': 0,
            'rate_start_time': time.perf_counter(),
            'rate_packet_count': 0,
            'addr': None,
        }
        self._client_slot_order.append(client_id)
        self.status_cb(f'[Player {slot}] "{name}" connected — virtual gamepad #{slot} created')
        self.telemetry_cb(f'PLAYER_JOIN|{client_id}|{name}|{color}|{slot}')
        return gp

    def _cleanup_stale_clients(self):
        """Remove clients that have timed out (no packets for 10+ seconds)."""
        now = time.time()
        stale = [cid for cid, info in self._clients.items() if now - info['last_time'] > 10.0]
        for cid in stale:
            info = self._clients[cid]
            if info['gamepad'] is not None:
                try:
                    info['gamepad'].reset()
                    info['gamepad'].update()
                except Exception:
                    pass
            self.status_cb(f'[Player {info["slot"]}] "{info["name"]}" disconnected (timeout)')
            self.telemetry_cb(f'PLAYER_LEAVE|{cid}|{info["name"]}|{info["color"]}|{info["slot"]}')
            del self._clients[cid]
            if cid in self._client_slot_order:
                self._client_slot_order.remove(cid)

    def get_connected_clients(self) -> list:
        """Return info about all connected clients for UI display."""
        result = []
        for cid, info in self._clients.items():
            result.append({
                'client_id': cid,
                'name': info['name'],
                'color': info['color'],
                'slot': info['slot'],
                'addr': info.get('addr'),
                'latency_samples': list(info.get('latency_samples', [])),
            })
        return result

    def _run(self):
        mode_str = 'multi-gamepad' if self.multi_gamepad else 'single'
        self.status_cb(f'listening on {self.bind_ip or "*"}:{self.port} ({mode_str} mode)')
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Increase receive buffer for bursty VPN traffic (256 KB)
        try:
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 262144)
        except Exception:
            pass
        self._sock.bind((self.bind_ip, self.port))

        if not self.multi_gamepad:
            self._init_single_gamepad()

        while not self._stop.is_set():
            try:
                self._sock.settimeout(0.5)
                data, addr = self._sock.recvfrom(2048)
            except socket.timeout:
                if self.multi_gamepad:
                    self._cleanup_stale_clients()
                else:
                    if self._owner and (time.time() - self._last_time_single) > 0.5:
                        self.status_cb('owner timeout, clearing state')
                        self._owner = None
                        self._last_seq_single = None
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

            # Security check
            allowed, reason = self._security.check_packet(state.client_id, addr[0], state.timestamp)
            if not allowed:
                if reason != "IP rate limit exceeded" or self._packet_count % 100 == 0:
                    self.status_cb(f'packet rejected from {addr}: {reason}')
                continue

            self._packet_count += 1

            if self.multi_gamepad:
                self._handle_multi(state, addr)
            else:
                self._handle_single(state, addr)

    def _handle_single(self, state, addr):
        """Legacy single-owner mode."""
        if self._owner is None:
            self._owner = state.client_id
            self.status_cb(f'owner set to {self._owner}')
        if state.client_id != self._owner:
            return
        if self._last_seq_single is not None:
            diff = (state.sequence - self._last_seq_single) & 0xFFFF
            if diff == 0:
                return
        self._last_seq_single = state.sequence
        self._last_time_single = time.time()
        self._update_telemetry_single(state)
        try:
            self._apply_state_single(state)
        except Exception as e:
            self.status_cb(f'apply state error: {e}')

    def _handle_multi(self, state, addr):
        """Multi-gamepad mode — each client_id gets its own virtual gamepad."""
        cid = state.client_id
        if cid not in self._clients:
            gp = self._get_or_create_gamepad(cid)
            if gp is None and cid not in self._clients:
                return  # max limit reached
        info = self._clients.get(cid)
        if info is None:
            return
        info['addr'] = addr
        # Seq check
        if info['last_seq'] is not None:
            diff = (state.sequence - info['last_seq']) & 0xFFFF
            if diff == 0:
                return
        info['last_seq'] = state.sequence
        info['last_time'] = time.time()
        self._update_telemetry_multi(state, cid)
        try:
            self._apply_state_multi(state, cid)
        except Exception as e:
            self.status_cb(f'[Player {info["slot"]}] apply error: {e}')

    # =======================  Button mapping (shared) =======================
    @staticmethod
    def _get_button_mapping():
        if not VGAME_AVAILABLE:
            return {}
        return {
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

    def _apply_gamepad(self, gamepad_obj, buttons: int, last_buttons: int, state) -> int:
        """Apply state to a virtual gamepad. Returns new last_buttons value."""
        if gamepad_obj is None:
            return buttons
        mapping = self._get_button_mapping()
        for bitmask, btn_enum in mapping.items():
            had = bool(last_buttons & bitmask)
            now = bool(buttons & bitmask)
            if now and not had:
                gamepad_obj.press_button(button=btn_enum)
            elif not now and had:
                gamepad_obj.release_button(button=btn_enum)
        lx = int(max(-32768, min(32767, state.lx)))
        ly = int(max(-32768, min(32767, state.ly)))
        rx = int(max(-32768, min(32767, state.rx)))
        ry = int(max(-32768, min(32767, state.ry)))
        gamepad_obj.left_joystick(lx, ly)
        gamepad_obj.right_joystick(rx, ry)
        lt = int(max(0, min(255, state.lt)))
        rt = int(max(0, min(255, state.rt)))
        gamepad_obj.left_trigger(lt)
        gamepad_obj.right_trigger(rt)
        gamepad_obj.update()
        return buttons

    # ==================  Single-mode apply  ==================
    def _apply_state_single(self, state):
        if self._vg_single is None:
            self.status_cb(f'recv seq={state.sequence} bt={state.buttons:#06x} lt={state.lt} rt={state.rt} lx={state.lx} ly={state.ly} rx={state.rx} ry={state.ry}')
            return
        try:
            self._last_buttons_single = self._apply_gamepad(
                self._vg_single, state.buttons, self._last_buttons_single, state)
        except Exception as e:
            self.status_cb(f'vgamepad apply error: {e}')

    # ==================  Multi-mode apply  ==================
    def _apply_state_multi(self, state, client_id: int):
        info = self._clients.get(client_id)
        if info is None:
            return
        gp = info['gamepad']
        if gp is None:
            return
        try:
            info['last_buttons'] = self._apply_gamepad(gp, state.buttons, info['last_buttons'], state)
        except Exception as e:
            self.status_cb(f'[Player {info["slot"]}] vgamepad error: {e}')
    
    # ==================  Telemetry helpers  ==================
    @staticmethod
    def _calc_latency(state) -> float:
        packet_time_s = state.timestamp / 1_000_000_000.0
        current_time_s = time.perf_counter_ns() / 1_000_000_000.0
        return (current_time_s - packet_time_s) * 1000

    def _update_telemetry_single(self, state):
        """Telemetry for legacy single mode."""
        current_time = time.perf_counter()
        latency_ms = self._calc_latency(state)
        self._latency_samples_single.append(latency_ms)
        if len(self._latency_samples_single) > 50:
            self._latency_samples_single.pop(0)
        if len(self._latency_samples_single) >= 2:
            import statistics
            jitter_ms = statistics.stdev(self._latency_samples_single)
        else:
            jitter_ms = 0.0
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
        if current_time - self._last_telemetry_time >= 1.0:
            if rate_hz > 0:
                self.telemetry_cb(f'Latency: {latency_ms:.1f}ms | Jitter: {jitter_ms:.1f}ms | Rate: {rate_hz:.1f}Hz | seq={state.sequence}')
            else:
                self.telemetry_cb(f'Latency: {latency_ms:.1f}ms | Jitter: {jitter_ms:.1f}ms | seq={state.sequence}')
            self._last_telemetry_time = current_time

    def _update_telemetry_multi(self, state, client_id: int):
        """Per-client telemetry for multi mode."""
        info = self._clients.get(client_id)
        if info is None:
            return
        current_time = time.perf_counter()
        latency_ms = self._calc_latency(state)
        info['latency_samples'].append(latency_ms)
        if len(info['latency_samples']) > 50:
            info['latency_samples'].pop(0)
        if len(info['latency_samples']) >= 2:
            import statistics
            jitter_ms = statistics.stdev(info['latency_samples'])
        else:
            jitter_ms = 0.0
        info['rate_packet_count'] = info.get('rate_packet_count', 0) + 1
        elapsed = current_time - info.get('rate_start_time', current_time)
        if elapsed >= 1.0:
            rate_hz = info['rate_packet_count'] / elapsed
            info['rate_start_time'] = current_time
            info['rate_packet_count'] = 0
        else:
            rate_hz = 0
        if current_time - info.get('last_telemetry_time', 0) >= 1.0:
            slot = info['slot']
            name = info['name']
            color = info['color']
            if rate_hz > 0:
                self.telemetry_cb(
                    f'PLAYER_STATS|{client_id}|{name}|{color}|{slot}|'
                    f'{latency_ms:.1f}|{jitter_ms:.1f}|{rate_hz:.1f}|{state.sequence}')
            else:
                self.telemetry_cb(
                    f'PLAYER_STATS|{client_id}|{name}|{color}|{slot}|'
                    f'{latency_ms:.1f}|{jitter_ms:.1f}|0|{state.sequence}')
            info['last_telemetry_time'] = current_time
    
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
