from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from utils.config import AppConfig


@dataclass
class AppState:
    config: AppConfig
    is_recording: bool = False
    is_busy: bool = False
    last_raw_text: Optional[str] = None
    last_clean_text: Optional[str] = None
    model_ready: bool = False
    model_error: Optional[str] = None
