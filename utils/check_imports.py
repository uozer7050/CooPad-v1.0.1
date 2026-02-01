import importlib
mods = [
    'customtkinter',
    'PIL',
    'pygame',
    'vgamepad',
    'gp.core.host'
]
for m in mods:
    try:
        importlib.import_module(m)
        print(f'OK {m}')
    except Exception as e:
        print(f'ERR {m}: {e}')
