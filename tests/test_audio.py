import threading
import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from bertytype.audio import capture
import wave
import struct
from pathlib import Path
from bertytype.audio import reader, vad


def test_start_recording_returns_bytes():
    sample = np.zeros((160, 1), dtype=np.int16)
    calls = []

    class FakeStream:
        def __init__(self, **kwargs):
            self._callback = kwargs["callback"]

        def __enter__(self):
            self._callback(sample, 160, None, None)
            return self

        def __exit__(self, *args):
            pass

    stop = threading.Event()
    stop.set()

    with patch("sounddevice.InputStream", FakeStream):
        result = capture.start_recording(stop)

    assert isinstance(result, bytes)
    assert len(result) > 0


def test_start_recording_empty_when_no_frames():
    class FakeStream:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    stop = threading.Event()
    stop.set()

    with patch("sounddevice.InputStream", FakeStream):
        result = capture.start_recording(stop)

    assert isinstance(result, bytes)


def _make_wav(path: Path, num_samples: int = 160, amplitude: int = 0) -> Path:
    with wave.open(str(path), "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(16000)
        f.writeframes(struct.pack(f"<{num_samples}h", *([amplitude] * num_samples)))
    return path


def test_read_file_wav_returns_bytes(tmp_path):
    wav = _make_wav(tmp_path / "clip.wav", num_samples=320, amplitude=1000)
    result = reader.read_file(wav)
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_read_file_normalises_to_16khz_mono(tmp_path):
    wav = _make_wav(tmp_path / "clip.wav", num_samples=320, amplitude=500)
    result = reader.read_file(wav)
    arr = np.frombuffer(result, dtype=np.int16)
    assert arr.ndim == 1


def test_trim_silence_removes_silent_audio():
    silence = np.zeros(16000, dtype=np.int16).tobytes()
    result = vad.trim_silence(silence, threshold=0.02)
    assert result == b""


def test_trim_silence_keeps_loud_audio():
    loud = (np.ones(16000, dtype=np.int16) * 10000).tobytes()
    result = vad.trim_silence(loud, threshold=0.02)
    assert len(result) > 0


def test_trim_silence_passthrough_when_all_active():
    audio = (np.ones(3200, dtype=np.int16) * 20000).tobytes()
    result = vad.trim_silence(audio, threshold=0.02)
    assert result == audio
