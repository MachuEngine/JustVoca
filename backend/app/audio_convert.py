# app/audio_convert.py
import subprocess
import os
import uuid  # 무작위 ID 생성을 위해 추가
from pathlib import Path
from typing import Union

# app/audio_convert.py 수정 제안
def convert_to_wav(input_path: Union[str, Path]) -> str:
    input_path = Path(input_path)
    out_wav_path = input_path.with_suffix(".wav")

    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-ar", "16000", "-ac", "1",
        "-acodec", "pcm_s16le", "-f", "wav", str(out_wav_path),
    ]
    try:
        # 에러 발생 시 로그를 남기도록 수정
        subprocess.check_call(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return str(out_wav_path)
    except Exception as e:
        print(f"[Conversion Error] FFmpeg 실패: {e}")
        return "" # 실패 시 빈 문자열 반환하여 API에서 차단하게 함