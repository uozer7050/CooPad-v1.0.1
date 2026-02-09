import threading
import time
import random
from typing import Callable, Optional


class BaseRunner:
    def __init__(self, status_cb: Callable[[str], None], telemetry_cb: Callable[[str], None]):
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.status_cb = status_cb
        self.telemetry_cb = telemetry_cb

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1.0)

    def _run(self):
        raise NotImplementedError()


class DummyHost(BaseRunner):
    def _run(self):
        self.status_cb("Host: starting (dummy)")
        seq = 0
        while not self._stop_event.is_set():
            time.sleep(0.5)
            latency = random.uniform(1.0, 8.0)
            self.telemetry_cb(f"Latency: {latency:.1f} ms | seq={seq}")
            seq = (seq + 1) & 0xFFFF
        self.status_cb("Host: stopped")


class DummyClient(BaseRunner):
    def _run(self):
        self.status_cb("Client: starting (dummy)")
        seq = 0
        while not self._stop_event.is_set():
            time.sleep(0.25)
            latency = random.uniform(0.5, 6.0)
            self.telemetry_cb(f"Sent seq={seq} | rtt~{latency:.1f} ms")
            seq = (seq + 1) & 0xFFFF
        self.status_cb("Client: stopped")


def _try_import_real():
    """Try to import real host/client implementations with detailed error reporting."""
    try:
        from gp.core.host import GamepadHost  # type: ignore
        from gp.core.client import GamepadClient  # type: ignore
        return GamepadHost, GamepadClient, None
    except ImportError as e:
        error_msg = f"Could not import gp.core modules: {str(e)}"
        return None, None, error_msg
    except Exception as e:
        error_msg = f"Unexpected error loading modules: {str(e)}"
        return None, None, error_msg


class GpController:
    def __init__(self, status_cb: Callable[[str], None], telemetry_cb: Callable[[str], None]):
        self.status_cb = status_cb
        self.telemetry_cb = telemetry_cb
        self.update_rate = 60  # Default update rate in Hz
        self.controller_profile = 'generic'  # Default controller profile
        # Network parameters
        self.client_target_ip = '127.0.0.1'  # Default client target IP
        self.client_port = 7777  # Default client port
        self.host_bind_ip = ''  # Default host bind IP (all interfaces)
        self.host_port = 7777  # Default host port
        HostCls, ClientCls, error = _try_import_real()
        self._host: BaseRunner
        self._client: BaseRunner
        if HostCls is not None and ClientCls is not None:
            # Wrap real classes to conform to start/stop interface
            class RealHost(BaseRunner):
                def __init__(inner_self, status_cb, telemetry_cb, parent):
                    super().__init__(status_cb, telemetry_cb)
                    inner_self.parent = parent
                
                def _run(inner_self):
                    try:
                        h = HostCls(
                            bind_ip=inner_self.parent.host_bind_ip,
                            port=inner_self.parent.host_port,
                            status_cb=inner_self.status_cb,
                            telemetry_cb=inner_self.telemetry_cb
                        )
                        inner_self.status_cb("✓ Host initialized successfully")
                        h.start()
                        while not inner_self._stop_event.is_set():
                            time.sleep(0.1)
                        h.stop()
                    except PermissionError as e:
                        inner_self.status_cb(f"✗ Permission denied: {e}")
                        inner_self.status_cb("→ Solution: Check system requirements and permissions")
                    except OSError as e:
                        inner_self.status_cb(f"✗ System error: {e}")
                        inner_self.status_cb("→ Check if virtual gamepad driver is installed")
                    except Exception as e:
                        inner_self.status_cb(f"✗ Host error: {e}")

            class RealClient(BaseRunner):
                def __init__(inner_self, status_cb, telemetry_cb, parent):
                    super().__init__(status_cb, telemetry_cb)
                    inner_self.parent = parent
                
                def _run(inner_self):
                    try:
                        c = ClientCls(
                            target_ip=inner_self.parent.client_target_ip,
                            port=inner_self.parent.client_port,
                            status_cb=inner_self.status_cb,
                            telemetry_cb=inner_self.telemetry_cb,
                            update_rate=inner_self.parent.update_rate,
                            controller_profile=inner_self.parent.controller_profile
                        )
                        inner_self.status_cb("✓ Client initialized successfully")
                        c.start()
                        while not inner_self._stop_event.is_set():
                            time.sleep(0.1)
                        c.stop()
                    except OSError as e:
                        inner_self.status_cb(f"✗ Network error: {e}")
                        inner_self.status_cb("→ Check firewall and network connectivity")
                    except Exception as e:
                        inner_self.status_cb(f"✗ Client error: {e}")

            # wrap callbacks to prefix messages with source
            self._host = RealHost(lambda t: status_cb(f"HOST|{t}"), lambda t: telemetry_cb(f"HOST|{t}"), self)
            self._client = RealClient(lambda t: status_cb(f"CLIENT|{t}"), lambda t: telemetry_cb(f"CLIENT|{t}"), self)
        else:
            if error:
                status_cb(f"⚠ {error}")
            status_cb("Using demo mode - Real gamepad functionality not available")
            status_cb("→ Check platform_help for setup instructions")
            self._host = DummyHost(lambda t: status_cb(f"HOST|{t}"), lambda t: telemetry_cb(f"HOST|{t}"))
            self._client = DummyClient(lambda t: status_cb(f"CLIENT|{t}"), lambda t: telemetry_cb(f"CLIENT|{t}"))

    def start_host(self):
        self._host.start()

    def stop_host(self):
        self._host.stop()

    def start_client(self):
        self._client.start()

    def stop_client(self):
        self._client.stop()
    
    def set_update_rate(self, rate: int):
        """Set the client update rate (30, 60, or 90 Hz)."""
        self.update_rate = rate
    
    def set_controller_profile(self, profile: str):
        """Set the controller profile ('generic', 'ps4', 'ps5', 'xbox360')."""
        self.controller_profile = profile
    
    def set_client_target(self, ip: str, port: int):
        """Set the client target IP address and port."""
        self.client_target_ip = ip
        self.client_port = port
    
    def set_host_config(self, bind_ip: str, port: int):
        """Set the host bind IP address and port."""
        self.host_bind_ip = bind_ip
        self.host_port = port
