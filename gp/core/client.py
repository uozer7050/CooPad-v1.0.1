import socket
import threading
import time
import random
from typing import Optional

from .protocol import make_state_from_inputs, pack, PROTOCOL_VERSION
from .controller_profiles import get_profile

try:
    import pygame
    PYGAME_AVAILABLE = True
except Exception:
    PYGAME_AVAILABLE = False


class GamepadClient:
    def __init__(self, target_ip: str = '127.0.0.1', port: int = 7777, client_id: int = None, status_cb=None, telemetry_cb=None, update_rate: int = 60, controller_profile: str = 'generic'):
        self.target_ip = target_ip
        self.port = port
        self.client_id = client_id if client_id is not None else random.getrandbits(32)
        self._sock: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._seq = 0
        self.status_cb = status_cb or (lambda s: print(f"CLIENT: {s}"))
        self.telemetry_cb = telemetry_cb or (lambda s: None)
        self.update_rate = update_rate  # Hz: 30, 60, or 90
        self._latency_samples = []
        self._last_telemetry_time = 0
        self.controller_profile = get_profile(controller_profile)

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1.0)

    def _run(self):
        self.status_cb(f'sending to {self.target_ip}:{self.port} id={self.client_id} @ {self.update_rate}Hz')
        self.status_cb(f'using controller profile: {self.controller_profile.name}')
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Explicitly bind to let OS assign a port immediately (prevents WinError 10022 on Windows)
        # Binding is only needed on Windows; on Unix-like systems, sendto() works without bind
        import platform
        if platform.system() == 'Windows':
            try:
                # lgtm [py/bind-socket-all-network-interfaces]
                # Bind to any interface (Windows requirement for UDP client sendto)
                # Security: This is a client socket that only sends data, not receives
                self._sock.bind(('', 0))
            except OSError as e:
                # If bind fails, log it but continue without explicit bind
                self.status_cb(f'socket bind failed (continuing anyway): {e}')
        update_interval = 1.0 / self.update_rate

        if not PYGAME_AVAILABLE:
            # send periodic heartbeats
            while not self._stop.is_set():
                send_time = time.perf_counter()
                state = make_state_from_inputs(self.client_id, self._seq, 0, 0, 0, 0, 0, 0, 0)
                self._sock.sendto(pack(state), (self.target_ip, self.port))
                self._update_telemetry(send_time)
                self._seq = (self._seq + 1) & 0xFFFF
                time.sleep(update_interval)
            return

        # initialize pygame joystick
        try:
            pygame.init()
            pygame.joystick.init()
            if pygame.joystick.get_count() == 0:
                self.status_cb('no joystick found; sending heartbeats')
            else:
                self.status_cb(f'joysticks: {pygame.joystick.get_count()}')
        except Exception as e:
            self.status_cb(f'pygame init error: {e}')

        while not self._stop.is_set():
            try:
                send_time = time.perf_counter()
                pygame.event.pump()
                if pygame.joystick.get_count() > 0:
                    js = pygame.joystick.Joystick(0)
                    js.init()
                    
                    # Get axes mapping from profile
                    axes_map = self.controller_profile.get_axes_mapping()
                    
                    # Read joystick axes based on profile
                    # Note: Y-axes are inverted (pygame: -1=up/1=down, XInput: -32768=down/32767=up)
                    lx = int(js.get_axis(axes_map['left_x']) * 32767) if js.get_numaxes() > axes_map['left_x'] else 0
                    ly = int(-js.get_axis(axes_map['left_y']) * 32767) if js.get_numaxes() > axes_map['left_y'] else 0
                    rx = int(js.get_axis(axes_map['right_x']) * 32767) if js.get_numaxes() > axes_map['right_x'] else 0
                    ry = int(-js.get_axis(axes_map['right_y']) * 32767) if js.get_numaxes() > axes_map['right_y'] else 0
                    
                    # Get button mapping from profile
                    button_map = self.controller_profile.get_button_mapping()
                    
                    # Map buttons using profile
                    buttons = 0
                    for b in range(js.get_numbuttons()):
                        if js.get_button(b) and b in button_map:
                            buttons |= button_map[b]
                    
                    # Check for DPad on hat if profile uses it
                    if self.controller_profile.uses_hat_for_dpad() and js.get_numhats() > 0:
                        hat = js.get_hat(0)
                        # hat returns (x, y) where x: -1=left, 0=center, 1=right; y: -1=down, 0=center, 1=up
                        if hat[1] == 1:  # up
                            buttons |= 0x0001
                        elif hat[1] == -1:  # down
                            buttons |= 0x0002
                        if hat[0] == -1:  # left
                            buttons |= 0x0004
                        elif hat[0] == 1:  # right
                            buttons |= 0x0008
                    
                    # Handle triggers based on profile
                    lt = 0
                    rt = 0
                    if axes_map['left_trigger'] is not None and js.get_numaxes() > axes_map['left_trigger']:
                        # Trigger on separate axis (PS4/PS5 style)
                        # pygame typically returns -1.0 (not pressed) to 1.0 (fully pressed)
                        # Convert to 0 (not pressed) to 255 (fully pressed)
                        lt_raw = js.get_axis(axes_map['left_trigger'])
                        lt = int((lt_raw + 1.0) * 127.5)
                        lt = max(0, min(255, lt))
                    
                    if axes_map['right_trigger'] is not None and js.get_numaxes() > axes_map['right_trigger']:
                        # Trigger on separate axis (PS4/PS5 style)
                        # pygame typically returns -1.0 (not pressed) to 1.0 (fully pressed)
                        # Convert to 0 (not pressed) to 255 (fully pressed)
                        rt_raw = js.get_axis(axes_map['right_trigger'])
                        rt = int((rt_raw + 1.0) * 127.5)
                        rt = max(0, min(255, rt))
                    
                    # Special case for Xbox 360: combined trigger axis
                    if hasattr(self.controller_profile, 'get_trigger_from_axis') and js.get_numaxes() > 2:
                        axis_2_value = js.get_axis(2)
                        lt, rt = self.controller_profile.get_trigger_from_axis(axis_2_value)
                else:
                    buttons = 0
                    lx = ly = rx = ry = 0
                    lt = rt = 0

                state = make_state_from_inputs(self.client_id, self._seq, buttons, lt, rt, lx, ly, rx, ry)
                self._sock.sendto(pack(state), (self.target_ip, self.port))
                self._update_telemetry(send_time)
                self._seq = (self._seq + 1) & 0xFFFF
                time.sleep(update_interval)
            except Exception as e:
                self.status_cb(f'send error: {e}')
                time.sleep(0.1)
    
    def _update_telemetry(self, send_time: float):
        """Calculate and report telemetry metrics."""
        current_time = time.perf_counter()
        
        # Simple latency estimation (time since packet sent)
        # In reality, we'd need server response for true RTT
        latency_ms = (current_time - send_time) * 1000
        
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
        
        # Report telemetry every second
        if current_time - self._last_telemetry_time >= 1.0:
            self.telemetry_cb(f'Latency: {latency_ms:.1f}ms | Jitter: {jitter_ms:.1f}ms | Rate: {self.update_rate}Hz | seq={self._seq}')
            self._last_telemetry_time = current_time
