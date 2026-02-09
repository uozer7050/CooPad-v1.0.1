import vgamepad
import inspect
print('vgamepad module:', vgamepad.__name__)
cls = getattr(vgamepad, 'VX360Gamepad', None)
print('VX360Gamepad found:', bool(cls))
if cls:
    print('public methods:')
    for m in [m for m in dir(cls) if not m.startswith('_')]:
        print(' -', m)
