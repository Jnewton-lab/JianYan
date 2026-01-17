from __future__ import annotations

from funasr import AutoModel


def main() -> None:
    AutoModel(
        model="iic/SenseVoiceSmall",
        vad_model="fsmn-vad",
        vad_kwargs={"max_single_segment_time": 30000},
        punc_model="ct-punc",
        device="cpu",
        disable_pbar=True,
    )
    print("models ready")


if __name__ == "__main__":
    main()
