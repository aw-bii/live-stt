import threading
import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
CHANNELS = 1


def start_recording(stop_event: threading.Event) -> bytes:
    frames: list[np.ndarray] = []

    def _callback(indata: np.ndarray, frame_count: int, time_info, status) -> None:
        frames.append(indata.copy())

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
        callback=_callback,
    ):
        stop_event.wait()

    if not frames:
        return b""
    return np.concatenate(frames, axis=0).tobytes()
