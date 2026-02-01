import socket
import threading
import time
import random
from typing import Optional

from .protocol import make_state_from_inputs, pack, PROTOCOL_VERSION

try:
    import pygame
    PYGAME_AVAILABLE = True
except Exception:
    PYGAME_AVAILABLE = False


class GamepadClient:
    def __init__(self, target_ip: str = '127.0.0.1', port: int = 7777, client_id: int = None, status_cb=None, telemetry_cb=None, update_rate: int = 60):
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
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
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
                    # basic mapping: axes 0/1 left, 2/3 right, triggers as buttons/axes depending
                    lx = int(js.get_axis(0) * 32767)
                    ly = int(js.get_axis(1) * 32767)
                    rx = int(js.get_axis(2) * 32767) if js.get_numaxes() > 2 else 0
                    ry = int(js.get_axis(3) * 32767) if js.get_numaxes() > 3 else 0
                    
                    # Map pygame button indices to protocol bits (matching host.py mapping)
                    # Protocol expects: 0x1000=A, 0x2000=B, 0x4000=X, 0x8000=Y
                    #                   0x0001=DPad_Up, 0x0002=DPad_Down, 0x0004=DPad_Left, 0x0008=DPad_Right
                    #                   0x0010=Start, 0x0020=Back, 0x0040=LThumb, 0x0080=RThumb
                    #                   0x0100=LShoulder, 0x0200=RShoulder
                    pygame_to_protocol = {
                        0: 0x1000,    # Button 0 (A) → bit 12
                        1: 0x2000,    # Button 1 (B) → bit 13
                        2: 0x4000,    # Button 2 (X) → bit 14
                        3: 0x8000,    # Button 3 (Y) → bit 15
                        4: 0x0100,    # Button 4 (Left Shoulder) → bit 8
                        5: 0x0200,    # Button 5 (Right Shoulder) → bit 9
                        6: 0x0020,    # Button 6 (Back/Select) → bit 5
                        7: 0x0010,    # Button 7 (Start) → bit 4
                        8: 0x0040,    # Button 8 (Left Thumb) → bit 6
                        9: 0x0080,    # Button 9 (Right Thumb) → bit 7
                        10: 0x0001,   # Button 10 (DPad Up) → bit 0
                        11: 0x0002,   # Button 11 (DPad Down) → bit 1
                        12: 0x0004,   # Button 12 (DPad Left) → bit 2
                        13: 0x0008,   # Button 13 (DPad Right) → bit 3
                    }
                    
                    buttons = 0
                    for b in range(min(14, js.get_numbuttons())):
                        if js.get_button(b) and b in pygame_to_protocol:
                            buttons |= pygame_to_protocol[b]
                    
                    # Check for DPad on hat (axis, common on many controllers)
                    if js.get_numhats() > 0:
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
                    lt = 0
                    rt = 0
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
