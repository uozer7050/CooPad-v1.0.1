import socket
import threading
import time
from typing import Optional

from .protocol import unpack, PROTOCOL_VERSION

try:
    import vgamepad as vg
    VGAME_AVAILABLE = True
except Exception:
    VGAME_AVAILABLE = False

# Try evdev/uinput as a Linux fallback for creating a virtual gamepad
try:
    from evdev import UInput, ecodes
    UINPUT_AVAILABLE = True
except Exception:
    UINPUT_AVAILABLE = False


class _UInputGamepad:
    """Minimal uinput-based virtual gamepad wrapper.

    Provides a subset of the vgamepad methods used by the host:
    - press_button / release_button
    - left_joystick / right_joystick (ABS axes)
    - left_trigger / right_trigger
    - update (synchronise)
    """
    def __init__(self):
        # define capabilities: axes and buttons
        cap = {
            ecodes.EV_KEY: [
                ecodes.BTN_A,
                ecodes.BTN_B,
                ecodes.BTN_X,
                ecodes.BTN_Y,
                ecodes.BTN_TL,
                ecodes.BTN_TR,
                ecodes.BTN_THUMBL,
                ecodes.BTN_THUMBR,
                ecodes.BTN_START,
                ecodes.BTN_SELECT,
            ],
            ecodes.EV_ABS: [
                (ecodes.ABS_X, (-32768, 32767, 0, 0)),
                (ecodes.ABS_Y, (-32768, 32767, 0, 0)),
                (ecodes.ABS_RX, (-32768, 32767, 0, 0)),
                (ecodes.ABS_RY, (-32768, 32767, 0, 0)),
                (ecodes.ABS_Z, (0, 255, 0, 0)),
                (ecodes.ABS_RZ, (0, 255, 0, 0)),
                (ecodes.ABS_HAT0X, (-1, 1, 0, 0)),
                (ecodes.ABS_HAT0Y, (-1, 1, 0, 0)),
            ],
        }
        try:
            self._ui = UInput(capabilities=cap, name="coopad-virtual-gamepad")
        except Exception:
            self._ui = None

    def press_button(self, button=None):
        if self._ui is None:
            return
        try:
            self._ui.write(ecodes.EV_KEY, button, 1)
        except Exception:
            pass

    def release_button(self, button=None):
        if self._ui is None:
            return
        try:
            self._ui.write(ecodes.EV_KEY, button, 0)
        except Exception:
            pass

    def left_joystick(self, x, y):
        if self._ui is None:
            return
        try:
            self._ui.write(ecodes.EV_ABS, ecodes.ABS_X, int(x))
            self._ui.write(ecodes.EV_ABS, ecodes.ABS_Y, int(y))
        except Exception:
            pass

    def right_joystick(self, x, y):
        if self._ui is None:
            return
        try:
            self._ui.write(ecodes.EV_ABS, ecodes.ABS_RX, int(x))
            self._ui.write(ecodes.EV_ABS, ecodes.ABS_RY, int(y))
        except Exception:
            pass

    def left_trigger(self, v):
        if self._ui is None:
            return
        try:
            self._ui.write(ecodes.EV_ABS, ecodes.ABS_Z, int(v))
        except Exception:
            pass

    def right_trigger(self, v):
        if self._ui is None:
            return
        try:
            self._ui.write(ecodes.EV_ABS, ecodes.ABS_RZ, int(v))
        except Exception:
            pass

    def update(self):
        if self._ui is None:
            return
        try:
            self._ui.syn()
        except Exception:
            pass


class GamepadHost:
    def __init__(self, bind_ip: str = "", port: int = 7777, status_cb=None, telemetry_cb=None):
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
        # Rate limiting: track packets per client
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
            try:
                self._vg = vg.VX360Gamepad()
                self.status_cb('vgamepad initialized')
            except Exception as e:
                self.status_cb(f'vgamepad init error: {e}')
        else:
            # Try to initialize a uinput-based virtual gamepad on Linux
            if UINPUT_AVAILABLE:
                try:
                    self._vg = _UInputGamepad()
                    self.status_cb('uinput virtual gamepad initialized')
                except Exception as e:
                    self.status_cb(f'uinput init error: {e}')

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
            
            # Rate limiting check
            if not self._check_rate_limit(state.client_id, addr):
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

        # Full XInput mapping per protocol.md (branch depending on backend)
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
            elif UINPUT_AVAILABLE:
                # mapping: protocol bits -> evdev button codes
                mapping = {
                    0x0001: ecodes.ABS_HAT0Y,  # DPad up handled via hat
                    0x0002: ecodes.ABS_HAT0Y,  # DPad down
                    0x0004: ecodes.ABS_HAT0X,  # left
                    0x0008: ecodes.ABS_HAT0X,  # right
                    0x0010: ecodes.BTN_START,
                    0x0020: ecodes.BTN_SELECT,
                    0x0040: ecodes.BTN_THUMBL,
                    0x0080: ecodes.BTN_THUMBR,
                    0x0100: ecodes.BTN_TL,
                    0x0200: ecodes.BTN_TR,
                    0x1000: ecodes.BTN_A,
                    0x2000: ecodes.BTN_B,
                    0x4000: ecodes.BTN_X,
                    0x8000: ecodes.BTN_Y,
                }
            else:
                mapping = {}

            # Press/release based on diff from last_buttons
            for bitmask, btn_enum in mapping.items():
                had = bool(self._last_buttons & bitmask)
                now = bool(buttons & bitmask)
                if now and not had:
                    # handle hat axes specially for uinput dpad
                    if UINPUT_AVAILABLE and btn_enum in (ecodes.ABS_HAT0X, ecodes.ABS_HAT0Y):
                        # set hat axis depending on which bit
                        if bitmask == 0x0001:  # up
                            self._vg.right_joystick(0, 0)  # noop fallback
                        else:
                            self._vg.right_joystick(0, 0)
                        # hat handling could be improved
                    else:
                        self._vg.press_button(button=btn_enum)
                elif not now and had:
                    if UINPUT_AVAILABLE and btn_enum in (ecodes.ABS_HAT0X, ecodes.ABS_HAT0Y):
                        self._vg.right_joystick(0, 0)
                    else:
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
    
    def _check_rate_limit(self, client_id: int, addr) -> bool:
        """Check if client is within rate limits. Returns True if allowed, False if blocked."""
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
