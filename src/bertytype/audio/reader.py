from pathlib import Path
import imageio_ffmpeg
from pydub import AudioSegment

AudioSegment.converter = imageio_ffmpeg.get_ffmpeg_exe()

SAMPLE_RATE = 16000


def read_file(path: Path) -> bytes:
    audio = AudioSegment.from_file(str(path))
    audio = audio.set_frame_rate(SAMPLE_RATE).set_channels(1).set_sample_width(2)
    return audio.raw_data
