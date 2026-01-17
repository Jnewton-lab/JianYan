from __future__ import annotations

import logging
import threading

import winsound

_sound_enabled = True


def _beep_sequence(pattern: list[tuple[int, int]]) -> None:
    """播放蜂鸣音序列，在后台线程执行避免阻塞"""
    global _sound_enabled
    if not _sound_enabled:
        return
    
    for freq, duration in pattern:
        try:
            winsound.Beep(freq, duration)
        except RuntimeError:
            # 无蜂鸣器驱动，尝试使用系统声音
            try:
                winsound.MessageBeep(winsound.MB_OK)
            except Exception:
                logging.debug("音效播放失败，已禁用")
                _sound_enabled = False
                return
        except Exception as e:
            logging.debug("音效播放错误: %s", e)
            _sound_enabled = False
            return


def _play_async(pattern: list[tuple[int, int]]) -> None:
    """异步播放音效"""
    t = threading.Thread(target=_beep_sequence, args=(pattern,), daemon=True)
    t.start()


def play_start_sound() -> None:
    """开始录音提示音 - 单声短促"""
    _play_async([(1000, 120)])


def play_stop_sound() -> None:
    """停止录音提示音 - 双声"""
    _play_async([(900, 100), (900, 100)])


def play_busy_sound() -> None:
    """忙碌提示音 - 三声低频"""
    _play_async([(500, 80), (500, 80), (500, 80)])


def play_processing_sound() -> None:
    """处理中提示音"""
    _play_async([(750, 120)])
