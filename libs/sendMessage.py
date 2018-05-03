from ctypes import byref, windll
from ctypes.wintypes import HWND, DWORD, UINT
import win32gui
import win32con
user32dll = windll.user32
__all__ = ['send', 'post']

def findProcessByID(procID):
    h = user32dll.GetTopWindow(0)
    while h:
        pid = DWORD(0)
        dwThreadId = user32dll.GetWindowThreadProcessId(h, byref(pid))
        if dwThreadId != 0:
            if pid.value == procID:
                return h
        h = user32dll.GetWindow(h, win32con.GW_HWNDNEXT)


def postMsgToChildWindow(hWnd, command, ID, eventType):
    hd = user32dll.GetWindow(hWnd, win32con.GW_HWNDNEXT)
    if hd:
        while hd:
            user32dll.PostMessageW(hd, command, 0, 0)
            hd = user32dll.GetWindow(hd, win32con.GW_HWNDNEXT)

def sendMsgToChildWindow(hWnd, command, ID, eventType):
    hd = user32dll.GetWindow(hWnd, win32con.GW_HWNDNEXT)
    if hd:
        while hd:
            user32dll.SendMessageW(hd, command, 0, 0)
            hd = user32dll.GetWindow(hd, win32con.GW_HWNDNEXT)


def post(procId, signalIDhex):
    target = findProcessByID(procId)
    if target:
        postMsgToChildWindow(target, signalIDhex, 0, 0)
    else:
        raise ValueError('没有找到指定的进程 ID :' + str(procId))

def send(procId, signalIDhex):
    target = findProcessByID(procId)
    if target:
        sendMsgToChildWindow(target, signalIDhex, 0, 0)
    else:
        raise ValueError('没有找到指定的进程 ID :' + str(procId))

