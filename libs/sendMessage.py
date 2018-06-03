from ctypes import byref, windll
from ctypes.wintypes import HWND, DWORD, UINT

import win32con
user32dll = windll.user32
__all__ = ['send', 'post']

def findProcessByID(procID):
    # FindWindowW https://msdn.microsoft.com/en-us/library/windows/desktop/ms633499(v=vs.85).aspx
    h = user32dll.FindWindowW('Appointed2_win_mainprogram', 'Appointed2 Windows 服务运行工具的信息接收')
    if h:
        pid = DWORD(0)
        dwThreadId = user32dll.GetWindowThreadProcessId(h, byref(pid))
        if dwThreadId != 0:
            if pid.value == procID:
                return h


# def postMsgToChildWindow(hWnd, command, ID, eventType):
#     hd = user32dll.GetWindow(hWnd, win32con.GW_HWNDNEXT)
#     if hd:
#         while hd:
#             user32dll.PostMessageW(hd, command, 0, 0)
#             hd = user32dll.GetWindow(hd, win32con.GW_HWNDNEXT)

# def sendMsgToChildWindow(hWnd, command, ID, eventType):
#     hd = user32dll.GetWindow(hWnd, win32con.GW_HWNDNEXT)
#     if hd:
#         while hd:
#             user32dll.SendMessageW(hd, command, 0, 0)
#             hd = user32dll.GetWindow(hd, win32con.GW_HWNDNEXT)


def post(procId, signalIDhex):
    target = findProcessByID(procId)
    if target:
        user32dll.PostMessageW(target, signalIDhex, 0, 0)
    else:
        raise ValueError('没有找到指定的进程 ID :' + str(procId))

def send(procId, signalIDhex):
    target = findProcessByID(procId)
    if target:
        user32dll.SendMessageW(target, signalIDhex, 0, 0)
    else:
        raise ValueError('没有找到指定的进程 ID :' + str(procId))

