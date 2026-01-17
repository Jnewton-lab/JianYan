from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from utils.paths import get_data_dir, get_model_cache_dir, get_temp_dir, require_writable_dir


def _get_config_path() -> Path:
    return get_data_dir() / "config.json"


@dataclass
class AppConfig:
    hotkey: str = "ctrl+shift+space"
    max_seconds: int = 300
    temp_dir: str = ""
    model_cache_dir: str = ""
    openai_api_key: str = ""
    openai_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    qwen_model: str = "qwen-flash"
    suppress_missing_llm_prompt: bool = False


def load_config() -> AppConfig:
    config_path = _get_config_path()
    if not config_path.exists():
        config = AppConfig()
        save_config(config)
        return config
    data = json.loads(config_path.read_text(encoding="utf-8"))
    valid_keys = {f.name for f in fields(AppConfig)}
    filtered = {k: v for k, v in data.items() if k in valid_keys}
    config = AppConfig(**filtered)
    config.temp_dir = _resolve_dir(config.temp_dir, get_temp_dir(), "临时文件")
    config.model_cache_dir = _resolve_dir(config.model_cache_dir, get_model_cache_dir(), "模型缓存")
    return config


def _resolve_dir(value: str, fallback: Path, label: str) -> str:
    if not value:
        return str(fallback)
    path = Path(value)
    if not path.is_absolute():
        path = fallback.parent / path
    require_writable_dir(path, label)
    return str(path)


def save_config(config: AppConfig) -> None:
    config_path = _get_config_path()
    config_path.write_text(json.dumps(asdict(config), ensure_ascii=False, indent=2), encoding="utf-8")
