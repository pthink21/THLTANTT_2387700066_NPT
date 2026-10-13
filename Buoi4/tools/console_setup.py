import ctypes
from ctypes import wintypes

k = ctypes.WinDLL('kernel32', use_last_error=True)
k.GetStdHandle.argtypes = [wintypes.DWORD]
k.GetStdHandle.restype = wintypes.HANDLE
k.GetConsoleMode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
k.SetConsoleMode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
handle = k.GetStdHandle(-10 & 0xffffffff)
mode = wintypes.DWORD()
if k.GetConsoleMode(handle, ctypes.byref(mode)):
    k.SetConsoleMode(handle, (mode.value | 0x0080) & ~0x0040)

class Font(ctypes.Structure):
    _fields_ = [('cbSize', wintypes.ULONG), ('nFont', wintypes.DWORD),
                ('dwFontSize', wintypes._COORD), ('FontFamily', wintypes.UINT),
                ('FontWeight', wintypes.UINT), ('FaceName', wintypes.WCHAR * 32)]

k.SetCurrentConsoleFontEx.argtypes = [wintypes.HANDLE, wintypes.BOOL, ctypes.POINTER(Font)]
font = Font()
font.cbSize = ctypes.sizeof(font)
font.dwFontSize.X = 0
font.dwFontSize.Y = 12
font.FontFamily = 54
font.FontWeight = 400
font.FaceName = 'Consolas'
k.SetCurrentConsoleFontEx(k.GetStdHandle(-11 & 0xffffffff), False, ctypes.byref(font))
