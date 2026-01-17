from __future__ import annotations

import threading
import time
import tkinter as tk
from tkinter import ttk
from typing import Callable


def show_startup_progress(
    root: tk.Tk,
    preload_func: Callable[[], None],
    estimate_seconds: int = 50,
    on_done: Callable[[str | None], None] | None = None,
) -> None:
    """显示启动加载进度条，直到 preload_func 完成。"""
    result: dict[str, str | None | bool] = {"done": False, "error": None}
    start_time = time.time()

    win = tk.Toplevel(root)
    win.title("模型加载中")
    win.geometry("420x180")
    win.resizable(False, False)
    win.protocol("WM_DELETE_WINDOW", lambda: None)
    win.transient(root)
    win.grab_set()

    tk.Label(win, text="正在加载本地语音模型", font=("Microsoft YaHei", 12)).pack(pady=(24, 6))
    tk.Label(win, text="预计约 50 秒，请稍候...", fg="#666666").pack(pady=(0, 12))

    progress_var = tk.DoubleVar(value=0.0)
    bar = ttk.Progressbar(win, length=340, variable=progress_var, maximum=100)
    bar.pack(pady=(0, 8))

    tk.Label(win, text="启动完成后将自动进入托盘", fg="#666666").pack()

    def _finish() -> None:
        progress_var.set(100)
        win.after(100, win.destroy)
        if on_done:
            on_done(result.get("error"))  # type: ignore[arg-type]

    def _worker() -> None:
        try:
            preload_func()
        except Exception as exc:  # pragma: no cover - UI thread gets status
            result["error"] = str(exc)
        finally:
            result["done"] = True
            root.after(0, _finish)

    def _staged_progress(elapsed: float) -> float:
        if elapsed <= 5:
            return 0.50 * (elapsed / 5.0)
        if elapsed <= 10:
            return 0.50 + 0.30 * ((elapsed - 5.0) / 5.0)
        if elapsed <= 15:
            return 0.80 + 0.10 * ((elapsed - 10.0) / 5.0)
        return 0.90 + 0.08 * min((elapsed - 15.0) / max(1.0, estimate_seconds - 15.0), 1.0)

    def _update_ui() -> None:
        if result["done"]:
            return
        elapsed = time.time() - start_time
        progress = min(_staged_progress(elapsed), 0.98)
        progress_var.set(progress * 100)
        win.after(100, _update_ui)

    worker = threading.Thread(target=_worker, daemon=True)
    worker.start()

    _center_window(win)
    win.after(100, _update_ui)


def _center_window(win: tk.Toplevel) -> None:
    win.update_idletasks()
    width = win.winfo_width()
    height = win.winfo_height()
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    x = max((screen_width - width) // 2, 0)
    y = max((screen_height - height) // 2, 0)
    win.geometry(f"{width}x{height}+{x}+{y}")
