from __future__ import annotations

import time

from dotenv import load_dotenv

from api.stt import transcribe_audio
from audio.recorder import Recorder
from utils.config import load_config


def main() -> None:
    load_dotenv()
    config = load_config()

    recorder = Recorder(max_seconds=5, sample_rate=16000)
    print("开始录音 3 秒...")
    recorder.start()
    time.sleep(3)
    result = recorder.stop()

    if not result.pcm_bytes:
        print("未获取到音频数据")
        return

    text = transcribe_audio(result.pcm_bytes, None, config)
    print("识别结果:")
    print(text)


if __name__ == "__main__":
    main()
