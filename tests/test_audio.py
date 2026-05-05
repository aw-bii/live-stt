import threading
import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from livesttt.audio import capture


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
