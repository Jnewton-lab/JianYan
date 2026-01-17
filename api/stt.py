from __future__ import annotations

import os
import re
import threading
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Optional

import numpy as np
import soundfile as sf

try:
    from funasr import AutoModel
    from funasr.utils.postprocess_utils import rich_transcription_postprocess
except Exception:  # pragma: no cover - optional dependency
    AutoModel = None
    rich_transcription_postprocess = None

from utils.config import AppConfig


@dataclass
class LocalModelConfig:
    model: str = "iic/SenseVoiceSmall"
    vad_model: str = "fsmn-vad"
    punc_model: str = "ct-punc"


_MODEL_LOCK = threading.Lock()
_MODEL: Optional[AutoModel] = None


def transcribe_audio(audio_bytes: bytes | None, temp_path: str | None, config: AppConfig) -> str:
    if audio_bytes is None and temp_path is None:
        raise ValueError("audio_bytes and temp_path are both None")
    if rich_transcription_postprocess is None:
        raise RuntimeError("未安装 funasr，请先安装本地模型依赖")

    wav_bytes = _load_bytes(audio_bytes, temp_path)
    if not wav_bytes:
        return ""

    audio, sample_rate = sf.read(BytesIO(wav_bytes), dtype="float32")
    if sample_rate != 16000:
        raise RuntimeError("录音采样率必须是 16kHz")

    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)

    model = _get_model()
    result = model.generate(
        input=audio,
        language="auto",
        use_itn=True,
        batch_size_s=60,
        merge_vad=True,
        merge_length_s=15,
    )
    text = result[0].get("text", "") if result else ""
    return _clean_transcript(rich_transcription_postprocess(text))


def preload_model() -> None:
    _get_model()


def _load_bytes(audio_bytes: bytes | None, temp_path: str | None) -> bytes:
    if temp_path:
        with open(temp_path, "rb") as f:
            return f.read()
    return audio_bytes or b""


def _get_local_model_paths() -> dict[str, str | None]:
    """检测本地是否已下载所有模型，返回各模型的本地路径"""
    from utils.paths import APP_ROOT
    models_base = APP_ROOT / "models" / "models" / "iic"
    
    paths = {
        "model": None,
        "vad_model": None,
        "punc_model": None,
    }
    
    # SenseVoiceSmall 主模型
    sense_path = models_base / "SenseVoiceSmall"
    if sense_path.exists() and (sense_path / "model.pt").exists():
        paths["model"] = str(sense_path)
    
    # VAD 模型
    vad_path = models_base / "speech_fsmn_vad_zh-cn-16k-common-pytorch"
    if vad_path.exists() and (vad_path / "model.pt").exists():
        paths["vad_model"] = str(vad_path)
    
    # 标点模型
    punc_path = models_base / "punc_ct-transformer_cn-en-common-vocab471067-large"
    if punc_path.exists() and (punc_path / "model.pt").exists():
        paths["punc_model"] = str(punc_path)
    
    return paths


def _get_model() -> AutoModel:
    global _MODEL
    if AutoModel is None:
        raise RuntimeError("未安装 funasr，请先安装本地模型依赖")
    if _MODEL is None:
        with _MODEL_LOCK:
            if _MODEL is None:
                model_cfg = LocalModelConfig()
                local_paths = _get_local_model_paths()
                
                # 优先使用本地路径，否则使用默认名称（会自动下载）
                model_path = local_paths["model"] or model_cfg.model
                vad_path = local_paths["vad_model"] or model_cfg.vad_model
                punc_path = local_paths["punc_model"] or model_cfg.punc_model
                
                _MODEL = AutoModel(
                    model=model_path,
                    vad_model=vad_path,
                    vad_kwargs={"max_single_segment_time": 30000},
                    punc_model=punc_path,
                    device=_detect_device(),
                    disable_pbar=True,
                    disable_update=True,  # 禁用更新检查
                    check_latest=False,  # 禁止联网检查模型更新
                )
    return _MODEL


def _detect_device() -> str:
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda:0"
    except Exception:
        return "cpu"
    return "cpu"


def _clean_transcript(text: str) -> str:
    if not text:
        return ""
    # 兼容两种标记格式: "<| zh |>" 和 "<|zh|>"
    text = re.sub(r"<\s*\|\s*[^|]+?\s*\|\s*>", "", text)
    text = re.sub(r"<\|\s*[^|]+?\s*\|>", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
