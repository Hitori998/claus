"""Windows global shortcut and paste. Never sends Enter or submits a form."""
import ctypes
from ctypes import wintypes

user32 = ctypes.WinDLL('user32', use_last_error=True)
user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
user32.GetAncestor.restype = wintypes.HWND


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
