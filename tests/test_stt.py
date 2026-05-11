import pytest
from bertytype.stt import engine


def test_transcribe_raises_without_backend():
    engine.set_backend(None)
    with pytest.raises(RuntimeError, match="STT backend not configured"):
        engine.transcribe(b"\x00" * 100)


def test_transcribe_calls_backend():
    engine.set_backend(lambda audio: "hello world")
    result = engine.transcribe(b"\x00" * 100)
    assert result == "hello world"


def test_set_backend_replaces_previous():
    engine.set_backend(lambda audio: "first")
    engine.set_backend(lambda audio: "second")
    assert engine.transcribe(b"\x00") == "second"


def test_transcribe_passes_audio_bytes_to_backend():
    received = []
    engine.set_backend(lambda audio: received.append(audio) or "ok")
    payload = b"\x01\x02\x03"
    engine.transcribe(payload)
    assert received[0] == payload
