"""Speech-to-text with word timestamps (faster-whisper, CPU, free)."""
import os
import subprocess

import numpy as np
from faster_whisper import WhisperModel


def _load_audio(path):
    """Decode with ffmpeg ourselves: avoids PyAV version breakage inside faster-whisper."""
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
        capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def transcribe(path, model_size=None, language=None):
    model_size = model_size or os.environ.get("WHISPER_MODEL", "small")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, info = model.transcribe(
        _load_audio(path), word_timestamps=True, vad_filter=True, language=language or None
    )
    out = []
    for s in segments:
        words = [
            {"start": w.start, "end": w.end, "word": w.word.strip()}
            for w in (s.words or [])
            if w.word.strip()
        ]
        out.append({"start": s.start, "end": s.end, "text": s.text.strip(), "words": words})
    return {"language": info.language, "duration": info.duration, "segments": out}
