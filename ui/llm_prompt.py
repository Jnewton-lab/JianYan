from __future__ import annotations

import ctypes


def _message_box(title: str, message: str, flags: int) -> int:
    user32 = ctypes.windll.user32
    return user32.MessageBoxW(0, message, title, flags)


def show_missing_llm_config_dialog() -> tuple[bool, bool]:
    """提示用户配置 LLM，返回(不再提示, 去设置)。"""
    MB_YESNOCANCEL = 0x00000003
    MB_ICONWARNING = 0x00000030
    IDYES = 6
    IDNO = 7

    message = (
        "AI 整理需要配置 OpenAI 兼容服务。\n"
        "请右键托盘图标 -> 设置，填写 Base URL 和 API Key。\n\n"
        "是否现在打开设置？\n"
        "【是】打开设置  【否】不再提示  【取消】仅关闭"
    )
    result = _message_box("需要配置 LLM", message, MB_YESNOCANCEL | MB_ICONWARNING)
    if result == IDYES:
        return False, True
    if result == IDNO:
        return True, False
    return False, False


def show_llm_auth_error_dialog(message: str) -> None:
    MB_OK = 0x00000000
    MB_ICONERROR = 0x00000010
    text = (
        "AI 整理失败：API Key 无效或未授权。\n"
        "请右键托盘图标 -> 设置，更新 OpenAI API Key。\n\n"
        f"错误信息：{message}"
    )
    _message_box("API Key 无效", text, MB_OK | MB_ICONERROR)
