from typing import Callable

# Plug in the VibeVoice transcription function here at app startup:
#   from vibeVoice import transcribe as vv_transcribe
#   engine.set_backend(vv_transcribe)
_backend: Callable[[bytes], str] | None = None


def set_backend(fn: Callable[[bytes], str] | None) -> None:
    global _backend
    _backend = fn


def transcribe(audio: bytes) -> str:
    if _backend is None:
        raise RuntimeError(
            "STT backend not configured. Call set_backend() with a VibeVoice callable."
        )
    return _backend(audio)
