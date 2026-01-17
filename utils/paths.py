from __future__ import annotations

import sys
import tempfile
from pathlib import Path


def _get_app_root() -> Path:
    """获取应用根目录，兼容打包和开发环境"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后，使用 EXE 所在目录
        return Path(sys.executable).parent
    else:
        # 开发环境，使用源码目录
        return Path(__file__).resolve().parents[1]


APP_ROOT = _get_app_root()


class PathAccessError(RuntimeError):
    pass


def _is_writable_dir(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path, delete=True):
            return True
    except Exception:
        return False


def require_writable_dir(path: Path, label: str) -> Path:
    if _is_writable_dir(path):
        return path
    raise PathAccessError(
        f"{label} 目录不可写，请将软件安装到普通可写目录（如 D:\\Apps 或 D:\\Tools），"
        "避免系统保护目录（如 C:\\Program Files）。"
    )


def get_data_dir() -> Path:
    return require_writable_dir(APP_ROOT / "data", "数据")


def get_model_cache_dir() -> Path:
    return require_writable_dir(APP_ROOT / "models", "模型缓存")


def get_temp_dir() -> Path:
    return require_writable_dir(APP_ROOT / "temp", "临时文件")
