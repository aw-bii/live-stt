import numpy as np

FRAME_MS = 30
SAMPLE_RATE = 16000


def trim_silence(audio: bytes, threshold: float = 0.02) -> bytes:
    if not audio:
        return b""
    samples = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768.0
    frame_size = int(SAMPLE_RATE * FRAME_MS / 1000)
    frames = [samples[i : i + frame_size] for i in range(0, len(samples), frame_size)]
    active = [f for f in frames if np.sqrt(np.mean(f ** 2)) > threshold]
    if not active:
        return b""
    return (np.concatenate(active) * 32768.0).astype(np.int16).tobytes()
