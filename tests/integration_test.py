"""Run a short integration test: start host and client, log activity.

Usage: python integration_test.py

If a physical joystick is attached (pygame), the client will send real inputs.
Otherwise the client will send periodic heartbeats. Logs are written to ./logs/*.log
"""
import os
import time
import threading
from gp.core.host import GamepadHost
from gp.core.client import GamepadClient
import pathlib


LOG_DIR = pathlib.Path(__file__).parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)


def make_logger(path):
    f = open(path, 'a', encoding='utf-8')

    def log(msg: str):
        ts = time.strftime('%Y-%m-%d %H:%M:%S')
        line = f'[{ts}] {msg}\n'
        f.write(line)
        f.flush()
        print(path.name.upper(), line, end='')

    return log


def run_test(duration=10):
    host_log = make_logger(LOG_DIR / 'host.log')
    client_log = make_logger(LOG_DIR / 'client.log')

    host = GamepadHost(status_cb=host_log)
    client = GamepadClient(target_ip='127.0.0.1', port=7777, status_cb=client_log)

    print('Starting host and client for', duration, 'seconds')
    host.start()
    time.sleep(0.2)
    client.start()

    try:
        for i in range(duration):
            time.sleep(1.0)
            print(f'... {i+1}/{duration}s')
    except KeyboardInterrupt:
        print('Interrupted')

    print('Stopping client and host')
    client.stop()
    host.stop()
    print('Logs written to', LOG_DIR)


if __name__ == '__main__':
    run_test(12)
