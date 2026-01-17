from __future__ import annotations

import logging
import queue
import threading
from typing import Callable, TypeVar

import tkinter as tk

T = TypeVar("T")

_task_queue: "queue.Queue[tuple[Callable[[tk.Tk], T], threading.Event, dict[str, object]]]" = queue.Queue()
_thread: threading.Thread | None = None
_ready = threading.Event()
_root: tk.Tk | None = None


def _tk_thread() -> None:
    global _root
    _root = tk.Tk()
    _root.withdraw()

    def _poll() -> None:
        while True:
            try:
                func, done, holder = _task_queue.get_nowait()
            except queue.Empty:
                break
            try:
                holder["result"] = func(_root)
            except Exception as exc:
                holder["error"] = exc
            finally:
                done.set()
        _root.after(50, _poll)

    _ready.set()
    _root.after(50, _poll)
    _root.mainloop()


def _ensure_thread() -> None:
    global _thread
    logging.info("[TkHost] _ensure_thread 被调用, _thread=%s, is_alive=%s", 
                 _thread, _thread.is_alive() if _thread else None)
    if _thread and _thread.is_alive():
        logging.info("[TkHost] Tk 线程已在运行")
        return
    logging.info("[TkHost] 正在启动新的 Tk 线程...")
    _ready.clear()
    _thread = threading.Thread(target=_tk_thread, daemon=True)
    _thread.start()
    logging.info("[TkHost] 等待 Tk 线程就绪...")
    _ready.wait()
    logging.info("[TkHost] Tk 线程已就绪")


def call_in_tk_thread(func: Callable[[tk.Tk], T]) -> T:
    logging.info("[TkHost] call_in_tk_thread 被调用")
    _ensure_thread()
    done = threading.Event()
    holder: dict[str, object] = {}
    logging.info("[TkHost] 将任务放入队列...")
    _task_queue.put((func, done, holder))
    logging.info("[TkHost] 等待任务完成...")
    done.wait()
    logging.info("[TkHost] 任务完成, error=%s", "error" in holder)
    if "error" in holder:
        raise holder["error"]  # type: ignore[misc]
    return holder["result"]  # type: ignore[return-value]
