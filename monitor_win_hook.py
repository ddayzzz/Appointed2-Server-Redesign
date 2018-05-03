# coding=utf-8
import ctypes
from ctypes.wintypes import WPARAM, LPARAM, MSG
__doc__ = 'Appointed2 注册的系统钩子，在 Windows 中管理由服务端发送的消息'
__all__ = ['regHook', 'init', 'destroy']
"""参考
http://nullege.com/codes/show/src@i@m@IMESupport-HEAD@imesupport@messagehook.py/45/ctypes.windll.user32.UnhookWindowsHookEx
"""
# Required pywin32
import win32gui
import win32con

hook_handle = None
hook_callback = None
__CLOSE_MESSAGE = 0x0400  # 默认的关闭信号
__RESTART_MESSAGE = 0x0401  # 默认的重启信号
__THREAD_ID = ctypes.windll.Kernel32.GetCurrentThreadId()
__PROCESSID = ctypes.windll.Kernel32.GetCurrentProcessId()
__CLOSE_CALL = None
__RESTART_CALL = None
__CTRLC_CALL = None
__WC = None


def message_hook_func(code, wParam, lParam):
    global hook_callback
    if hook_callback is not None:
        msg = ctypes.cast(lParam, ctypes.POINTER(MSG))
        hook_callback(msg[0].hWnd, msg[0].message, msg[0].wParam, msg[0].lParam)
    res = int()
    try:
        res = ctypes.windll.user32.CallNextHookEx(hook_handle, code, wParam, lParam)
    except ctypes.ArgumentError as e:
        pass
    return res
 


prototype = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_long, WPARAM, LPARAM)
proc_obj = prototype(message_hook_func)


# def setup_postMessage(callback):
#     global hook_handle
#     global hook_callback
#     global __THREAD_ID
#
#     hook_handle = ctypes.windll.user32.SetWindowsHookExW(
#         win32con.WH_GETMESSAGE, proc_obj, 0,
#         __THREAD_ID)
#     if hook_handle == 0:
#         hook_handle = None
#         raise Exception('注册 Appointed2 系统钩子失败 : API:SetWindowsHookExW 调用失败。')
#     hook_callback = callback
 
def destroy():
    global __WC
    ctypes.windll.user32.UnhookWindowsHookEx(hook_handle)
    win32gui.UnregisterClass(__WC.lpszClassName, None)  # 解除注册
 
def init(close_signalnum, restartsignalnum, closecall, restartcall, ctrlccall):
    global __CLOSE_MESSAGE
    global __RESTART_MESSAGE
    global __CLOSE_CALL
    global __RESTART_CALL
    global __CTRLC_CALL
    __CLOSE_CALL = closecall
    __RESTART_CALL = restartcall
    __CLOSE_MESSAGE = close_signalnum
    __RESTART_MESSAGE = restartsignalnum
    __CTRLC_CALL = ctrlccall


def regHook():
    global __CLOSE_MESSAGE
    global __RESTART_MESSAGE
    global __PROCESSID
 
    # def on_create(hwnd):
    #     def on_receive_postedMessage(hwnd, msg, wParam, lParam):
    #         if msg == __CLOSE_MESSAGE:
    #             if callable(__CLOSE_CALL):
    #                 __CLOSE_CALL(0,0)
    #             return 0
    #         elif msg == __RESTART_MESSAGE:
    #             if callable(__RESTART_CALL):
    #                 __RESTART_CALL(0,0)
    #             return 0
    #         return None
    #
    #     setup_postMessage(on_receive_postedMessage)

    def OnClose(hwnd, msg, wparam, lparam):
        """Destroy window when it is closed by user"""
        # __CLOSE_CALL()  # 如果是用户按 ctrl+c 取消的话，还是发送 http 消息吧/xk
        __CTRLC_CALL()
        win32gui.DestroyWindow(hwnd)

    def OnClose_Call(hwnd, msg, wparam, lparam):
        """Destroy window when it is closed by user"""
        __CLOSE_CALL()

    def OnRestart_Call(hwnd, msg, wparam, lparam):
        """Destroy window when it is closed by user"""
        __RESTART_CALL()


    def OnDestroy(hwnd, msg, wparam, lparam):
        """Quit application when window is destroyed"""
        win32gui.PostQuitMessage(0)
 
    #Define message map for window
    wndproc = {
            win32con.WM_CLOSE: OnClose,
            win32con.WM_DESTROY: OnDestroy,
            win32con.WM_MOUSEMOVE: OnClose,
            __CLOSE_MESSAGE: OnClose_Call,
            __RESTART_MESSAGE: OnRestart_Call
            }

    def CreateWindow(title, message_map, location):
        global __WC
        """Create a window with defined title, message map, and rectangle"""
        l, t, r, b = location
        wc = win32gui.WNDCLASS()
        wc.lpszClassName = 'Appointed2_win_mainprogram'
        wc.lpfnWndProc = message_map
        win32gui.RegisterClass(wc)
        hwnd = win32gui.CreateWindow(wc.lpszClassName,
            title,
            win32con.WS_CAPTION | win32con.WS_SYSMENU | win32con.WS_VISIBLE,
            l, t, r, b, 0, 0, 0, None)
        ctypes.windll.user32.ShowWindow(hwnd, win32con.SW_HIDE)
        __WC = wc
        # on_create(hwnd)
        return hwnd, wc

    # print(__PROCESSID)
    # print(__THREAD_ID)
    #Display sample window
    return CreateWindow('Appointed2 Windows 服务运行工具的信息接收', wndproc, (0,0,0,0))