from __future__ import annotations

import logging
import time

import keyboard

_logger = logging.getLogger(__name__)


def _write_clipboard_win32(text: str) -> bool:
    """使用 win32clipboard 写入剪贴板（如果可用）"""
    try:
        import win32clipboard
        import win32con
        
        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
            _logger.info("[Paste] win32clipboard 写入成功")
            return True
        finally:
            win32clipboard.CloseClipboard()
    except ImportError:
        _logger.debug("[Paste] win32clipboard 不可用")
        return False
    except Exception as e:
        _logger.warning("[Paste] win32clipboard 写入失败: %s", e)
        return False


def _write_clipboard_ctypes(text: str) -> bool:
    """使用 ctypes 写入剪贴板（不依赖外部库）"""
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        user32.OpenClipboard.argtypes = [wintypes.HWND]
        user32.OpenClipboard.restype = wintypes.BOOL
        user32.CloseClipboard.argtypes = []
        user32.CloseClipboard.restype = wintypes.BOOL
        user32.EmptyClipboard.argtypes = []
        user32.EmptyClipboard.restype = wintypes.BOOL
        user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
        user32.SetClipboardData.restype = wintypes.HANDLE

        kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
        kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
        kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalLock.restype = wintypes.LPVOID
        kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalUnlock.restype = wintypes.BOOL

        CF_UNICODETEXT = 13
        GMEM_MOVEABLE = 0x0002

        for _ in range(5):
            if user32.OpenClipboard(None):
                break
            time.sleep(0.05)
        else:
            _logger.warning("[Paste] OpenClipboard 失败: %d", ctypes.get_last_error())
            return False
        try:
            if not user32.EmptyClipboard():
                _logger.warning("[Paste] EmptyClipboard 失败: %d", ctypes.get_last_error())
                return False

            data = text + "\0"
            size = len(data) * ctypes.sizeof(ctypes.c_wchar)
            hglobal = kernel32.GlobalAlloc(GMEM_MOVEABLE, size)
            if not hglobal:
                _logger.warning("[Paste] GlobalAlloc 失败: %d", ctypes.get_last_error())
                return False

            locked = kernel32.GlobalLock(hglobal)
            if not locked:
                _logger.warning("[Paste] GlobalLock 失败: %d", ctypes.get_last_error())
                return False

            try:
                ctypes.memmove(locked, ctypes.c_wchar_p(data), size)
            finally:
                kernel32.GlobalUnlock(hglobal)

            if not user32.SetClipboardData(CF_UNICODETEXT, hglobal):
                _logger.warning("[Paste] SetClipboardData 失败: %d", ctypes.get_last_error())
                return False

            _logger.info("[Paste] ctypes 写入成功")
            return True
        finally:
            user32.CloseClipboard()
    except Exception as e:
        _logger.warning("[Paste] ctypes 写入失败: %s", e)
        return False


def _read_clipboard_ctypes() -> str | None:
    """使用 ctypes 读取剪贴板内容，用于校验"""
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        user32.OpenClipboard.argtypes = [wintypes.HWND]
        user32.OpenClipboard.restype = wintypes.BOOL
        user32.CloseClipboard.argtypes = []
        user32.CloseClipboard.restype = wintypes.BOOL
        user32.GetClipboardData.argtypes = [wintypes.UINT]
        user32.GetClipboardData.restype = wintypes.HANDLE

        kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalLock.restype = wintypes.LPVOID
        kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalUnlock.restype = wintypes.BOOL

        CF_UNICODETEXT = 13

        if not user32.OpenClipboard(None):
            return None
        try:
            handle = user32.GetClipboardData(CF_UNICODETEXT)
            if not handle:
                return None
            locked = kernel32.GlobalLock(handle)
            if not locked:
                return None
            try:
                text = ctypes.wstring_at(locked)
            finally:
                kernel32.GlobalUnlock(handle)
            return text
        finally:
            user32.CloseClipboard()
    except Exception:
        return None


def write_clipboard(text: str) -> None:
    """写入剪贴板，尝试多种方法"""
    if not text:
        _logger.warning("[Paste] text 为空，跳过写入剪贴板")
        return
    
    _logger.info("[Paste] 写入剪贴板，文本长度: %d", len(text))
    
    # 方法1: win32clipboard (最可靠)
    if _write_clipboard_win32(text):
        return

    # 方法2: ctypes (不依赖外部库)
    if _write_clipboard_ctypes(text):
        return

    _logger.error("[Paste] 所有剪贴板写入方法都失败了")


def write_clipboard_and_paste(text: str) -> None:
    """写入剪贴板并模拟 Ctrl+V 粘贴"""
    if not text:
        _logger.warning("[Paste] text 为空，跳过粘贴")
        return

    write_clipboard(text)
    verify_text = _read_clipboard_ctypes()
    if verify_text != text:
        _logger.warning("[Paste] 剪贴板校验失败")

    # 等待剪贴板内容生效
    time.sleep(0.1)

    _logger.info("[Paste] 模拟 Ctrl+V 粘贴...")
    
    # 方法1: 尝试 keybd_event（更兼容旧应用）
    if _send_ctrl_v_keybd_event():
        return
    
    # 方法2: 尝试 SendInput
    if _send_ctrl_v_sendinput():
        return
    
    # 方法3: 回退到 keyboard 库
    try:
        _release_modifiers()
        time.sleep(0.05)
        keyboard.press_and_release("ctrl+v")
        _logger.info("[Paste] keyboard Ctrl+V 发送完成")
    except Exception as e:
        _logger.exception("[Paste] keyboard 模拟粘贴失败: %s", e)


def _release_modifiers() -> None:
    for key in ("ctrl", "shift", "alt", "win"):
        try:
            keyboard.release(key)
        except Exception:
            pass


def _send_ctrl_v_keybd_event() -> bool:
    """使用 keybd_event 发送 Ctrl+V（更兼容旧应用）"""
    try:
        import ctypes
        
        user32 = ctypes.windll.user32
        
        VK_CONTROL = 0x11
        VK_V = 0x56
        KEYEVENTF_KEYUP = 0x0002
        
        # 按下 Ctrl
        user32.keybd_event(VK_CONTROL, 0, 0, 0)
        # 按下 V
        user32.keybd_event(VK_V, 0, 0, 0)
        # 释放 V
        user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
        # 释放 Ctrl
        user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
        
        _logger.info("[Paste] keybd_event Ctrl+V 发送完成")
        return True
    except Exception as e:
        _logger.warning("[Paste] keybd_event 失败: %s", e)
        return False


def _release_all_modifiers_sendinput() -> None:
    """使用 SendInput 释放所有修饰键"""
    try:
        import ctypes
        from ctypes import wintypes
        import sys
        
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        
        KEYEVENTF_KEYUP = 0x0002
        VK_CONTROL = 0x11
        VK_SHIFT = 0x10
        VK_MENU = 0x12  # Alt
        VK_LWIN = 0x5B
        VK_RWIN = 0x5C
        
        if hasattr(wintypes, 'ULONG_PTR'):
            ULONG_PTR = wintypes.ULONG_PTR
        elif sys.maxsize > 2**32:
            ULONG_PTR = ctypes.c_uint64
        else:
            ULONG_PTR = ctypes.c_uint32

        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [
                ("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ULONG_PTR),
            ]

        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [
                ("dx", wintypes.LONG),
                ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ULONG_PTR),
            ]

        class HARDWAREINPUT(ctypes.Structure):
            _fields_ = [
                ("uMsg", wintypes.DWORD),
                ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD),
            ]

        class INPUT_UNION(ctypes.Union):
            _fields_ = [
                ("mi", MOUSEINPUT),
                ("ki", KEYBDINPUT),
                ("hi", HARDWAREINPUT),
            ]

        class INPUT(ctypes.Structure):
            _fields_ = [
                ("type", wintypes.DWORD),
                ("union", INPUT_UNION),
            ]

        def make_key_up(vk: int) -> INPUT:
            inp = INPUT()
            inp.type = 1  # INPUT_KEYBOARD
            inp.union.ki.wVk = vk
            inp.union.ki.dwFlags = KEYEVENTF_KEYUP
            return inp

        # 释放 Ctrl, Shift, Alt, Win
        inputs = (INPUT * 5)(
            make_key_up(VK_CONTROL),
            make_key_up(VK_SHIFT),
            make_key_up(VK_MENU),
            make_key_up(VK_LWIN),
            make_key_up(VK_RWIN),
        )
        
        count = user32.SendInput(5, ctypes.byref(inputs), ctypes.sizeof(INPUT))
        _logger.info("[Paste] 释放修饰键完成, 发送 %d/5 个", count)
    except Exception as e:
        _logger.warning("[Paste] 释放修饰键失败: %s", e)


def _send_ctrl_v_sendinput() -> bool:
    """使用 SendInput 发送 Ctrl+V，返回是否成功。"""
    try:
        import ctypes
        from ctypes import wintypes
        import sys

        user32 = ctypes.WinDLL("user32", use_last_error=True)

        INPUT_KEYBOARD = 1
        KEYEVENTF_KEYUP = 0x0002
        VK_CONTROL = 0x11
        VK_V = 0x56
        
        # ULONG_PTR 在某些 Python 版本中不存在，手动定义
        if hasattr(wintypes, 'ULONG_PTR'):
            ULONG_PTR = wintypes.ULONG_PTR
        elif sys.maxsize > 2**32:
            ULONG_PTR = ctypes.c_uint64
        else:
            ULONG_PTR = ctypes.c_uint32

        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [
                ("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ULONG_PTR),
            ]

        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [
                ("dx", wintypes.LONG),
                ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ULONG_PTR),
            ]

        class HARDWAREINPUT(ctypes.Structure):
            _fields_ = [
                ("uMsg", wintypes.DWORD),
                ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD),
            ]

        class INPUT_UNION(ctypes.Union):
            _fields_ = [
                ("mi", MOUSEINPUT),
                ("ki", KEYBDINPUT),
                ("hi", HARDWAREINPUT),
            ]

        class INPUT(ctypes.Structure):
            _fields_ = [
                ("type", wintypes.DWORD),
                ("union", INPUT_UNION),
            ]

        def make_keyboard_input(vk: int, flags: int = 0) -> INPUT:
            inp = INPUT()
            inp.type = INPUT_KEYBOARD
            inp.union.ki.wVk = vk
            inp.union.ki.wScan = 0
            inp.union.ki.dwFlags = flags
            inp.union.ki.time = 0
            inp.union.ki.dwExtraInfo = 0
            return inp

        inputs = (INPUT * 4)(
            make_keyboard_input(VK_CONTROL),
            make_keyboard_input(VK_V),
            make_keyboard_input(VK_V, KEYEVENTF_KEYUP),
            make_keyboard_input(VK_CONTROL, KEYEVENTF_KEYUP),
        )
        
        count = user32.SendInput(4, ctypes.byref(inputs), ctypes.sizeof(INPUT))
        if count == 4:
            _logger.info("[Paste] SendInput Ctrl+V 发送完成")
            return True
        else:
            err = ctypes.get_last_error()
            _logger.warning("[Paste] SendInput 只发送了 %d/4 个输入, 错误码: %d", count, err)
            return False
    except Exception as exc:
        _logger.warning("[Paste] SendInput 失败: %s", exc)
        return False
