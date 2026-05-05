from pathlib import Path
import wave
import numpy as np
from scipy.interpolate import interp1d

SAMPLE_RATE = 16000


def read_file(path: Path) -> bytes:
    with wave.open(str(path), "rb") as wav_file:
        n_channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        framerate = wav_file.getframerate()
        n_frames = wav_file.getnframes()

        # Read audio data
        audio_bytes = wav_file.readframes(n_frames)
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16).reshape(-1, n_channels)

        # Convert to mono if needed
        if n_channels > 1:
            audio_array = np.mean(audio_array, axis=1).astype(np.int16)
        else:
            audio_array = audio_array.flatten()

        # Resample if needed
        if framerate != SAMPLE_RATE:
            original_time = np.arange(len(audio_array)) / framerate
            new_length = int(len(audio_array) * SAMPLE_RATE / framerate)
            new_time = np.arange(new_length) / SAMPLE_RATE
            f = interp1d(original_time, audio_array, kind='linear', fill_value='extrapolate')
            audio_array = f(new_time).astype(np.int16)

        # Ensure sample width is 2 bytes (16-bit)
        if sample_width != 2:
            audio_array = (audio_array * (2 / sample_width)).astype(np.int16)

        return audio_array.tobytes()
