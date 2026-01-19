import subprocess
from pathlib import Path
from typing import Union

def convert_to_wav(input_path: Union[str, Path]) -> str:
    input_path = Path(input_path)
    out_wav_path = input_path.with_suffix(".wav")

    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-ar", "16000", "-ac", "1",
        "-acodec", "pcm_s16le", "-f", "wav", str(out_wav_path),
    ]
    try:
        subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return str(out_wav_path)
    except Exception:
        return str(input_path)