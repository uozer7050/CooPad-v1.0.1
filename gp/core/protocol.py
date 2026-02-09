import struct
import time
from dataclasses import dataclass

PACKET_FMT = '<B I H H B B h h h h Q'  # matches protocol.md
PACKET_SIZE = struct.calcsize(PACKET_FMT)
PROTOCOL_VERSION = 2
MAX_PACKET_SIZE = 1024  # Maximum allowed packet size
MIN_PACKET_SIZE = PACKET_SIZE  # Minimum valid packet size


@dataclass
class GamepadState:
    version: int
    client_id: int
    sequence: int
    buttons: int
    lt: int
    rt: int
    lx: int
    ly: int
    rx: int
    ry: int
    timestamp: int


def validate_packet_size(data: bytes) -> bool:
    """Validate packet size is within acceptable bounds."""
    size = len(data)
    return MIN_PACKET_SIZE <= size <= MAX_PACKET_SIZE


def validate_gamepad_state(state: GamepadState) -> bool:
    """Validate gamepad state values are within acceptable ranges."""
    # Version check
    if state.version != PROTOCOL_VERSION:
        return False
    
    # Button mask should be 16 bits max
    if state.buttons > 0xFFFF:
        return False
    
    # Triggers should be 0-255
    if not (0 <= state.lt <= 255 and 0 <= state.rt <= 255):
        return False
    
    # Joysticks should be in range -32768 to 32767
    for val in [state.lx, state.ly, state.rx, state.ry]:
        if not (-32768 <= val <= 32767):
            return False
    
    # Sequence should be 16 bits
    if state.sequence > 0xFFFF:
        return False
    
    return True


def pack(state: GamepadState) -> bytes:
    return struct.pack(
        PACKET_FMT,
        state.version,
        state.client_id,
        state.sequence,
        state.buttons,
        state.lt,
        state.rt,
        state.lx,
        state.ly,
        state.rx,
        state.ry,
        state.timestamp,
    )


def unpack(data: bytes) -> GamepadState:
    if not validate_packet_size(data):
        raise ValueError(f'invalid packet size: {len(data)} bytes')
    if len(data) < PACKET_SIZE:
        raise ValueError('packet too small')
    vals = struct.unpack(PACKET_FMT, data[:PACKET_SIZE])
    state = GamepadState(*vals)
    if not validate_gamepad_state(state):
        raise ValueError('invalid gamepad state values')
    return state


def make_state_from_inputs(client_id: int, seq: int, buttons: int, lt: int, rt: int, lx: int, ly: int, rx: int, ry: int) -> GamepadState:
    return GamepadState(
        version=PROTOCOL_VERSION,
        client_id=client_id,
        sequence=seq & 0xFFFF,
        buttons=buttons & 0xFFFF,
        lt=lt & 0xFF,
        rt=rt & 0xFF,
        lx=int(lx),
        ly=int(ly),
        rx=int(rx),
        ry=int(ry),
        timestamp=time.perf_counter_ns(),
    )
