from __future__ import annotations

import logging
from collections.abc import Callable

import keyboard


_hotkey_id: int | None = None
_logger = logging.getLogger(__name__)


def start_hotkey_listener(on_toggle: Callable[[], None], hotkey: str) -> None:
    global _hotkey_id
    _logger.info("[Hotkey] 注册快捷键: %s", hotkey)
    stop_hotkey_listener()
    
    def _wrapped_callback():
        _logger.info("[Hotkey] >>> 快捷键被触发! <<<")
        try:
            on_toggle()
            _logger.info("[Hotkey] on_toggle 回调完成")
        except Exception as e:
            _logger.exception("[Hotkey] on_toggle 回调异常: %s", e)
    
    _hotkey_id = keyboard.add_hotkey(hotkey, _wrapped_callback, suppress=True)
    _logger.info("[Hotkey] 快捷键注册成功, id=%s", _hotkey_id)


def stop_hotkey_listener() -> None:
    global _hotkey_id
    if _hotkey_id is not None:
        _logger.info("[Hotkey] 移除快捷键, id=%s", _hotkey_id)
        keyboard.remove_hotkey(_hotkey_id)
        _hotkey_id = None
