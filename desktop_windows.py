"""Windows global shortcut and paste. Never sends Enter or submits a form."""
import ctypes
from ctypes import wintypes
import uuid

user32 = ctypes.WinDLL('user32', use_last_error=True)
user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
user32.GetAncestor.restype = wintypes.HWND


class GUID(ctypes.Structure):
    _fields_ = [('data', ctypes.c_ubyte * 16)]

    def __init__(self, value):
        super().__init__((ctypes.c_ubyte * 16).from_buffer_copy(uuid.UUID(value).bytes_le))


class PROPERTYKEY(ctypes.Structure):
    _fields_ = [('fmtid', GUID), ('pid', wintypes.DWORD)]


class PROPVARIANT(ctypes.Structure):
    _fields_ = [('vt', wintypes.WORD), ('reserved1', wintypes.WORD),
                ('reserved2', wintypes.WORD), ('reserved3', wintypes.WORD),
                ('value', ctypes.c_void_p), ('padding', ctypes.c_void_p)]


def set_taskbar_identity(hwnd, launcher, icon):
    # A Python-hosted window needs its own Shell identity and relaunch metadata.
    shell = ctypes.WinDLL('shell32')
    shell.SHGetPropertyStoreForWindow.argtypes = [wintypes.HWND, ctypes.POINTER(GUID), ctypes.POINTER(ctypes.c_void_p)]
    shell.SHGetPropertyStoreForWindow.restype = ctypes.c_long
    store = ctypes.c_void_p()
    hr = shell.SHGetPropertyStoreForWindow(hwnd, ctypes.byref(GUID('886d8eeb-8cf2-4446-8d02-cdba1dbdcf99')), ctypes.byref(store))
    if hr < 0:
        raise OSError(f'Windows Shell property store: {hr:#x}')
    table = ctypes.cast(store, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
    set_value = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.POINTER(PROPERTYKEY), ctypes.POINTER(PROPVARIANT))(table[6])
    try:
        for pid, text in ((2, f'"{launcher}"'), (3, f'{icon},0'), (4, 'Claus'), (5, 'Claus.Ditado.Local')):
            buffer = ctypes.create_unicode_buffer(text)
            value = PROPVARIANT(vt=31, value=ctypes.cast(buffer, ctypes.c_void_p))
            key = PROPERTYKEY(GUID('9f4c2855-9f79-4b39-a8d0-e1d42de1d5f3'), pid)
            hr = set_value(store, ctypes.byref(key), ctypes.byref(value))
            if hr < 0: raise OSError(f'Windows Shell property {pid}: {hr:#x}')
        hr = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p)(table[7])(store)
        if hr < 0: raise OSError(f'Windows Shell commit: {hr:#x}')
    finally:
        ctypes.WINFUNCTYPE(wintypes.ULONG, ctypes.c_void_p)(table[2])(store)


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [('wVk', wintypes.WORD), ('wScan', wintypes.WORD), ('dwFlags', wintypes.DWORD),
                ('time', wintypes.DWORD), ('dwExtraInfo', ctypes.c_size_t)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [('dx', wintypes.LONG), ('dy', wintypes.LONG), ('mouseData', wintypes.DWORD),
                ('dwFlags', wintypes.DWORD), ('time', wintypes.DWORD), ('dwExtraInfo', ctypes.c_size_t)]


class InputUnion(ctypes.Union):
    _fields_ = [('ki', KEYBDINPUT), ('mi', MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ('data',)
    _fields_ = [('type', wintypes.DWORD), ('data', InputUnion)]


def foreground():
    return int(user32.GetForegroundWindow() or 0)


def modifiers_down():
    return any(user32.GetAsyncKeyState(key) & 0x8000 for key in (0x10, 0x11, 0x12, 0x5B, 0x5C))


def paste_shortcut():
    events = (INPUT * 4)(
        INPUT(type=1, ki=KEYBDINPUT(wVk=0x11)), INPUT(type=1, ki=KEYBDINPUT(wVk=0x56)),
        INPUT(type=1, ki=KEYBDINPUT(wVk=0x56, dwFlags=2)), INPUT(type=1, ki=KEYBDINPUT(wVk=0x11, dwFlags=2)))
    if user32.SendInput(4, events, ctypes.sizeof(INPUT)) != 4:
        raise OSError('O Windows bloqueou a inserção. Use Copiar e cole manualmente.')
