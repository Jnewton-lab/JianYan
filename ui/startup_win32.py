from __future__ import annotations

import threading
import time
from typing import Callable


def show_startup_progress(
    preload_func: Callable[[], None],
    estimate_seconds: int = 120,
) -> tuple[bool, str | None]:
    """使用 tkinter 显示现代风格的启动进度窗口"""
    import tkinter as tk
    from tkinter import ttk

    result: dict[str, str | None | bool] = {"done": False, "error": None}
    start_time = time.time()
    root: tk.Tk | None = None

    def _worker() -> None:
        try:
            preload_func()
        except Exception as exc:
            result["error"] = str(exc)
        finally:
            result["done"] = True

    def _staged_progress(elapsed: float) -> float:
        """分阶段进度模拟"""
        if elapsed <= 5:
            return 0.50 * (elapsed / 5.0)
        if elapsed <= 10:
            return 0.50 + 0.30 * ((elapsed - 5.0) / 5.0)
        if elapsed <= 15:
            return 0.80 + 0.10 * ((elapsed - 10.0) / 5.0)
        return 0.90 + 0.08 * min((elapsed - 15.0) / max(1.0, estimate_seconds - 15.0), 1.0)

    def _update_progress() -> None:
        if result["done"]:
            progress_var.set(100)
            root.after(200, root.destroy)
            return
        
        elapsed = time.time() - start_time
        pct = min(_staged_progress(elapsed), 0.98)
        progress_var.set(int(pct * 100))
        
        # 更新状态文字
        if elapsed < 5:
            status_label.config(text="正在初始化语音识别引擎...")
        elif elapsed < 10:
            status_label.config(text="正在加载 SenseVoice 模型...")
        elif elapsed < 20:
            status_label.config(text="正在加载 VAD 模型...")
        elif elapsed < 40:
            status_label.config(text="正在加载标点模型...")
        else:
            status_label.config(text="即将完成...")
        
        root.after(50, _update_progress)

    # 启动后台加载线程
    threading.Thread(target=_worker, daemon=True).start()

    # 创建窗口
    root = tk.Tk()
    root.title("语音识别服务")
    root.overrideredirect(True)  # 无边框
    root.attributes("-topmost", True)  # 置顶
    root.configure(bg="#1e1e1e")
    
    # 窗口尺寸和位置
    width, height = 400, 200
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    x = (screen_w - width) // 2
    y = (screen_h - height) // 2
    root.geometry(f"{width}x{height}+{x}+{y}")

    # 圆角效果 (Windows 11)
    try:
        from ctypes import windll, byref, c_int
        HWND = windll.user32.GetForegroundWindow()
        DWMWA_WINDOW_CORNER_PREFERENCE = 33
        DWMWCP_ROUND = 2
        windll.dwmapi.DwmSetWindowAttribute(HWND, DWMWA_WINDOW_CORNER_PREFERENCE, byref(c_int(DWMWCP_ROUND)), 4)
    except Exception:
        pass

    # 主框架
    main_frame = tk.Frame(root, bg="#1e1e1e", padx=30, pady=25)
    main_frame.pack(fill="both", expand=True)

    # 图标和标题
    title_frame = tk.Frame(main_frame, bg="#1e1e1e")
    title_frame.pack(fill="x", pady=(0, 15))
    
    icon_label = tk.Label(title_frame, text="🎙️", font=("Segoe UI Emoji", 28), bg="#1e1e1e", fg="white")
    icon_label.pack(side="left")
    
    title_label = tk.Label(
        title_frame, 
        text="语音识别服务启动中", 
        font=("Microsoft YaHei UI", 16, "bold"), 
        bg="#1e1e1e", 
        fg="white"
    )
    title_label.pack(side="left", padx=(10, 0))

    # 进度条样式
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "Custom.Horizontal.TProgressbar",
        troughcolor="#3a3a3a",
        background="#0078d4",
        darkcolor="#0078d4",
        lightcolor="#0078d4",
        bordercolor="#1e1e1e",
        thickness=10
    )

    # 进度条
    progress_var = tk.IntVar(value=0)
    progress_bar = ttk.Progressbar(
        main_frame,
        variable=progress_var,
        maximum=100,
        style="Custom.Horizontal.TProgressbar",
        length=340
    )
    progress_bar.pack(pady=(10, 15))

    # 状态文字
    status_label = tk.Label(
        main_frame,
        text="正在初始化...",
        font=("Microsoft YaHei UI", 10),
        bg="#1e1e1e",
        fg="#a0a0a0"
    )
    status_label.pack()

    # 提示文字
    hint_label = tk.Label(
        main_frame,
        text="✨ 启动完成后将自动最小化到系统托盘",
        font=("Microsoft YaHei UI", 9),
        bg="#1e1e1e",
        fg="#606060"
    )
    hint_label.pack(pady=(15, 0))

    # 允许拖动窗口
    def start_move(event):
        root._drag_start_x = event.x
        root._drag_start_y = event.y
    
    def do_move(event):
        x = root.winfo_x() + event.x - root._drag_start_x
        y = root.winfo_y() + event.y - root._drag_start_y
        root.geometry(f"+{x}+{y}")
    
    root.bind("<Button-1>", start_move)
    root.bind("<B1-Motion>", do_move)

    # 开始更新进度
    root.after(50, _update_progress)

    # 运行主循环
    root.mainloop()

    ok = result.get("error") is None
    return ok, result.get("error")
