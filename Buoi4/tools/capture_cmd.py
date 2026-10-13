"""Launch real CMD consoles and capture their Windows screen rectangles."""
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import subprocess
import sys
import time
from PIL import ImageGrab

BASE = Path(__file__).resolve().parents[1]
WORK = BASE / 'working'
USER = ctypes.WinDLL('user32', use_last_error=True)
USER.SetProcessDPIAware()
USER.SetForegroundWindow.argtypes = [wintypes.HWND]
USER.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
USER.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
USER.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
USER.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
CALLBACK = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
USER.EnumWindows.argtypes = [CALLBACK, wintypes.LPARAM]
USER.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]


def window(title):
    found = []
    @CALLBACK
    def visit(hwnd, arg):
        name = ctypes.create_unicode_buffer(1024)
        USER.GetWindowTextW(hwnd, name, 1024)
        if title in name.value:
            found.append(hwnd)
        return True
    USER.EnumWindows(visit, 0)
    return found[0] if found else None


def launch(label, command, number, filename=None, live=False):
    title = f'LAB04-CMD-{number} - NGUYEN PHUC THINH - 2387700066 - {label}'
    batch = WORK / f'cmd-{number}.bat'
    marker = WORK / f'cmd-{number}-done.txt'
    if marker.exists():
        marker.unlink()
    preview = 'echo ' + command.splitlines()[0]
    body = f'''@echo off
chcp 65001 >nul
title {title}
"{sys.executable}" tools\\console_setup.py
mode con: cols=125 lines=52
color 0F
cd /d "{BASE}"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
echo ===================================================================
echo  LAB 04 - WEB APP AND API SECURITY
echo  NGUYEN PHUC THINH - MSSV 2387700066
echo  {label}
echo ===================================================================
echo.
echo {BASE}^>
{preview}
{command}
set "LAB_EXIT=%errorlevel%"
echo.
echo Exit code: %LAB_EXIT%
echo %LAB_EXIT% > "{marker}"
'''
    batch.write_text(body, encoding='utf-8')
    existing = window(title)
    if existing:
        USER.PostMessageW(existing, 0x0010, 0, 0)
        time.sleep(.3)
    process = subprocess.Popen(['conhost.exe', 'cmd.exe', '/k', str(batch)], cwd=BASE)
    time.sleep(1)
    deadline = time.monotonic() + 100
    while time.monotonic() < deadline:
        if live:
            import socket
            try:
                with socket.create_connection(('127.0.0.1', 5100), timeout=.5):
                    break
            except OSError:
                pass
        elif marker.exists():
            code = marker.read_text().strip()
            if code != '0':
                raise RuntimeError(f'{label} failed with exit code {code}')
            break
        time.sleep(.3)
    else:
        raise TimeoutError(label)
    hwnd = window(title)
    for _ in range(30):
        if hwnd:
            break
        time.sleep(.1)
        hwnd = window(title)
    if not hwnd:
        raise RuntimeError('CMD window not found: ' + title)
    USER.ShowWindow(hwnd, 9)
    USER.PostMessageW(hwnd, 0x0100, 27, 0)
    USER.PostMessageW(hwnd, 0x0101, 27, 0)
    USER.SetWindowPos(hwnd, -1, 50, 50, 1330, 970, 0x0040)
    USER.SetForegroundWindow(hwnd)
    time.sleep(.8)
    rect = wintypes.RECT()
    if not USER.GetWindowRect(hwnd, ctypes.byref(rect)):
        raise ctypes.WinError()
    dest = BASE / 'screenshots' / filename if filename else WORK / f'cmd-{number}.png'
    ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom)).save(dest)
    USER.SetWindowPos(hwnd, -2, 0, 0, 0, 0, 0x0001 | 0x0002)
    print(f'CAPTURED {label}: {dest}', flush=True)
    return process
