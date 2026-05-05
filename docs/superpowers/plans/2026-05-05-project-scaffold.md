# Project Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold the full `live-stt` project - every file, interface, stub, and test - so the repo is installable, all modules are importable, and the test suite runs green from day one.

**Architecture:** `src/` layout Python package (`livestt`) wired through a single `__main__.py` orchestrator. Each subsystem (audio, stt, llm, injection, hotkeys, ui) lives in its own subpackage with one clear public function; no cross-module imports except through `__main__.py` and `config.py`. VibeVoice STT is stubbed with an injectable backend so it can be wired up independently.

**Tech Stack:** Python 3.11+, hatchling (build), sounddevice + numpy (mic capture), pydub (file reading), pystray + Pillow (tray), keyboard (hotkeys), pyperclip + pyautogui (text injection), requests (Ollama HTTP), pytest + pytest-mock (tests)

---

## File Map

Files created in this plan:

```text
pyproject.toml
tests/__init__.py
tests/test_config.py
tests/test_audio.py
tests/test_stt.py
tests/test_llm.py
tests/test_injection.py
tests/test_hotkeys.py
src/livestt/__init__.py
src/livesttt/__main__.py
src/livesttt/config.py
src/livesttt/audio/__init__.py
src/livesttt/audio/capture.py
src/livesttt/audio/reader.py
src/livesttt/audio/vad.py
src/livesttt/stt/__init__.py
src/livesttt/stt/engine.py
src/livesttt/llm/__init__.py
src/livesttt/llm/prompts.py
src/livesttt/llm/client.py
src/livesttt/injection/__init__.py
src/livesttt/injection/injector.py
src/livesttt/injection/exporter.py
src/livesttt/hotkeys/__init__.py
src/livesttt/hotkeys/daemon.py
src/livesttt/ui/__init__.py
src/livesttt/ui/tray.py
src/livesttt/ui/settings.py
```

---

### Task 1: pyproject.toml and dev environment

**Files:**
- Create: `pyproject.toml`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "live-stt"
version = "0.1.0"
description = "Local voice dictation powered by VibeVoice and Gemma 4"
requires-python = ">=3.11"
dependencies = [
    "sounddevice>=0.4",
    "numpy>=1.24",
    "pydub>=0.25",
    "pystray>=0.19",
    "Pillow>=10.0",
    "keyboard>=0.13",
    "pywin32>=306",
    "pyperclip>=1.8",
    "pyautogui>=0.9",
    "requests>=2.31",
]

[project.optional-dependencies]
dev = ["pytest>=7", "pytest-mock>=3"]

[project.scripts]
livestt = "livesttt.__main__:main"

[tool.hatch.build.targets.wheel]
packages = ["src/livesttt"]
```

- [ ] **Step 2: Create virtualenv and install**

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

Expected: `Successfully installed live-stt-0.1.0 ...`

- [ ] **Step 3: Verify entry point is importable**

```bash
python -c "import livesttt; print('ok')"
```

Expected: This will fail with `ModuleNotFoundError` until Task 2 creates the package - that's expected here.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "feat: add pyproject.toml with hatchling build and all dependencies"
```

---

### Task 2: Package root

**Files:**
- Create: `src/livesttt/__init__.py`
- Create: `src/livesttt/__main__.py`

- [ ] **Step 1: Create package root**

`src/livesttt/__init__.py`:
```python
__version__ = "0.1.0"
```

- [ ] **Step 2: Create __main__.py stub**

`src/livesttt/__main__.py`:
```python
def main() -> None:
    print("livesttt starting...")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Verify import and entry point**

```bash
python -c "import livesttt; print(livesttt.__version__)"
python -m livesttt
```

Expected output:
```
0.1.0
livesttt starting...
```

- [ ] **Step 4: Commit**

```bash
git add src/
git commit -m "feat: add package root with version and main stub"
```

---

### Task 3: config.py

**Files:**
- Create: `src/livesttt/config.py`
- Create: `tests/__init__.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write the failing tests**

`tests/__init__.py`: empty file.

`tests/test_config.py`:
```python
import json
from pathlib import Path
import pytest
from livesttt import config


def test_defaults():
    cfg = config.Config()
    assert cfg.hotkey == "ctrl+shift+space"
    assert cfg.model == "gemma4"
    assert cfg.refine is True
    assert cfg.vad_threshold == 0.02


def test_save_and_load(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "config.json")
    cfg = config.Config(hotkey="ctrl+r", model="gemma4", refine=False, vad_threshold=0.05)
    config.save(cfg)
    loaded = config.load()
    assert loaded.hotkey == "ctrl+r"
    assert loaded.refine is False
    assert loaded.vad_threshold == 0.05


def test_load_missing_returns_defaults(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "nonexistent.json")
    cfg = config.load()
    assert cfg == config.Config()


def test_save_creates_parent_dir(tmp_path, monkeypatch):
    target = tmp_path / "nested" / "dir" / "config.json"
    monkeypatch.setattr(config, "CONFIG_PATH", target)
    config.save(config.Config())
    assert target.exists()
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_config.py -v
```

Expected: 4 errors - `cannot import name 'config'`

- [ ] **Step 3: Implement config.py**

`src/livesttt/config.py`:
```python
import json
from dataclasses import dataclass, asdict
from pathlib import Path

CONFIG_PATH = Path.home() / ".livesttt" / "config.json"


@dataclass
class Config:
    hotkey: str = "ctrl+shift+space"
    model: str = "gemma4"
    refine: bool = True
    vad_threshold: float = 0.02


def load() -> Config:
    if CONFIG_PATH.exists():
        return Config(**json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
    return Config()


def save(cfg: Config) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(asdict(cfg), indent=2), encoding="utf-8")
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_config.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/livesttt/config.py tests/
git commit -m "feat: add config.py with load/save and default settings"
```

---

### Task 4: audio/capture.py

**Files:**
- Create: `src/livesttt/audio/__init__.py`
- Create: `src/livesttt/audio/capture.py`
- Test in: `tests/test_audio.py`

- [ ] **Step 1: Write the failing test**

`tests/test_audio.py`:
```python
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
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_audio.py::test_start_recording_returns_bytes tests/test_audio.py::test_start_recording_empty_when_no_frames -v
```

Expected: 2 errors - `cannot import name 'capture'`

- [ ] **Step 3: Create audio/__init__.py and capture.py**

`src/livesttt/audio/__init__.py`: empty file.

`src/livesttt/audio/capture.py`:
```python
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
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_audio.py::test_start_recording_returns_bytes tests/test_audio.py::test_start_recording_empty_when_no_frames -v
```

Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/livesttt/audio/ tests/test_audio.py
git commit -m "feat: add audio/capture.py with push-to-talk recording"
```

---

### Task 5: audio/reader.py and audio/vad.py

**Files:**
- Create: `src/livesttt/audio/reader.py`
- Create: `src/livesttt/audio/vad.py`
- Extend: `tests/test_audio.py`

- [ ] **Step 1: Write failing tests**

First, add these imports to the top of `tests/test_audio.py` (after the existing imports):
```python
import wave
import struct
from pathlib import Path
from livesttt.audio import reader, vad
```

Then append these test functions to the bottom of `tests/test_audio.py`:

```python
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
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_audio.py -k "reader or vad or wav or silence" -v
```

Expected: 5 errors - `cannot import name 'reader'` / `cannot import name 'vad'`

- [ ] **Step 3: Implement reader.py**

`src/livesttt/audio/reader.py`:
```python
from pathlib import Path
from pydub import AudioSegment

SAMPLE_RATE = 16000


def read_file(path: Path) -> bytes:
    audio = AudioSegment.from_file(str(path))
    audio = audio.set_frame_rate(SAMPLE_RATE).set_channels(1).set_sample_width(2)
    return audio.raw_data
```

- [ ] **Step 4: Implement vad.py**

`src/livesttt/audio/vad.py`:
```python
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
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_audio.py -v
```

Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git add src/livesttt/audio/reader.py src/livesttt/audio/vad.py tests/test_audio.py
git commit -m "feat: add audio/reader.py and audio/vad.py"
```

---

### Task 6: stt/engine.py

**Files:**
- Create: `src/livesttt/stt/__init__.py`
- Create: `src/livesttt/stt/engine.py`
- Create: `tests/test_stt.py`

The VibeVoice API is not yet known, so `engine.py` uses an injectable backend. The VibeVoice call gets wired in at app startup via `set_backend()`.

- [ ] **Step 1: Write the failing tests**

`tests/test_stt.py`:
```python
import pytest
from livesttt.stt import engine


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
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_stt.py -v
```

Expected: 4 errors - `cannot import name 'engine'`

- [ ] **Step 3: Implement engine.py**

`src/livesttt/stt/__init__.py`: empty file.

`src/livesttt/stt/engine.py`:
```python
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
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_stt.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/livesttt/stt/ tests/test_stt.py
git commit -m "feat: add stt/engine.py with injectable VibeVoice backend"
```

---

### Task 7: llm/prompts.py and llm/client.py

**Files:**
- Create: `src/livesttt/llm/__init__.py`
- Create: `src/livesttt/llm/prompts.py`
- Create: `src/livesttt/llm/client.py`
- Create: `tests/test_llm.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_llm.py`:
```python
import pytest
from unittest.mock import patch, MagicMock
from livesttt.llm import prompts, client


def test_get_prompt_clean_up_contains_text():
    result = prompts.get_prompt("clean_up", "um hello world")
    assert "hello world" in result


def test_get_prompt_rewrite_contains_text():
    result = prompts.get_prompt("rewrite", "gonna do stuff")
    assert "gonna do stuff" in result


def test_get_prompt_unknown_mode_raises():
    with pytest.raises(ValueError, match="Unknown mode"):
        prompts.get_prompt("blah", "text")


def test_refine_posts_to_ollama():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"response": "  cleaned text  "}
    mock_resp.raise_for_status = MagicMock()

    with patch("requests.post", return_value=mock_resp) as mock_post:
        result = client.refine("um hello", "clean_up", "gemma4")

    assert result == "cleaned text"
    call_kwargs = mock_post.call_args
    payload = call_kwargs[1]["json"] if "json" in call_kwargs[1] else call_kwargs[0][1]
    assert payload["model"] == "gemma4"


def test_refine_raises_on_http_error():
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = Exception("500")

    with patch("requests.post", return_value=mock_resp):
        with pytest.raises(Exception, match="500"):
            client.refine("text", "clean_up", "gemma4")


def test_refine_strips_whitespace():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"response": "\n  result \n"}
    mock_resp.raise_for_status = MagicMock()

    with patch("requests.post", return_value=mock_resp):
        result = client.refine("text", "rewrite", "gemma4")

    assert result == "result"
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_llm.py -v
```

Expected: 6 errors - `cannot import name 'prompts'`

- [ ] **Step 3: Implement prompts.py**

`src/livesttt/llm/__init__.py`: empty file.

`src/livesttt/llm/prompts.py`:
```python
_TEMPLATES: dict[str, str] = {
    "clean_up": (
        "Clean up the following speech transcript. Fix grammar, remove filler words "
        "(um, uh, like), and add punctuation. Output only the cleaned text:\n\n{text}"
    ),
    "rewrite": (
        "Rewrite the following speech transcript as polished prose. "
        "Output only the rewritten text:\n\n{text}"
    ),
}


def get_prompt(mode: str, text: str) -> str:
    if mode not in _TEMPLATES:
        raise ValueError(f"Unknown mode: {mode!r}. Choose from {list(_TEMPLATES)}")
    return _TEMPLATES[mode].format(text=text)
```

- [ ] **Step 4: Implement client.py**

`src/livesttt/llm/client.py`:
```python
import requests
from livesttt.llm.prompts import get_prompt

OLLAMA_URL = "http://localhost:11434/api/generate"


def refine(text: str, mode: str, model: str) -> str:
    payload = {
        "model": model,
        "prompt": get_prompt(mode, text),
        "stream": False,
    }
    resp = requests.post(OLLAMA_URL, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()["response"].strip()
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_llm.py -v
```

Expected: 6 passed

- [ ] **Step 6: Commit**

```bash
git add src/livesttt/llm/ tests/test_llm.py
git commit -m "feat: add llm/prompts.py and llm/client.py for Ollama/Gemma 4"
```

---

### Task 8: injection/injector.py

**Files:**
- Create: `src/livesttt/injection/__init__.py`
- Create: `src/livesttt/injection/injector.py`
- Create: `tests/test_injection.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_injection.py`:
```python
from unittest.mock import patch, call, MagicMock
from livesttt.injection import injector


def test_inject_copies_text_to_clipboard():
    with patch("pyperclip.copy") as mock_copy, \
         patch("pyautogui.hotkey"), \
         patch("time.sleep"):
        injector.inject("hello world")
    mock_copy.assert_called_once_with("hello world")


def test_inject_sends_ctrl_v():
    with patch("pyperclip.copy"), \
         patch("pyautogui.hotkey") as mock_hotkey, \
         patch("time.sleep"):
        injector.inject("hello world")
    mock_hotkey.assert_called_once_with("ctrl", "v")


def test_inject_sleeps_before_paste():
    sleep_calls = []
    with patch("pyperclip.copy"), \
         patch("pyautogui.hotkey"), \
         patch("time.sleep", side_effect=sleep_calls.append):
        injector.inject("text")
    assert len(sleep_calls) == 1
    assert sleep_calls[0] > 0


def test_inject_empty_string():
    with patch("pyperclip.copy") as mock_copy, \
         patch("pyautogui.hotkey"), \
         patch("time.sleep"):
        injector.inject("")
    mock_copy.assert_called_once_with("")
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_injection.py -v
```

Expected: 4 errors - `cannot import name 'injector'`

- [ ] **Step 3: Implement injector.py**

`src/livesttt/injection/__init__.py`: empty file.

`src/livesttt/injection/injector.py`:
```python
import time
import pyperclip
import pyautogui

_PASTE_DELAY = 0.05


def inject(text: str) -> None:
    pyperclip.copy(text)
    time.sleep(_PASTE_DELAY)
    pyautogui.hotkey("ctrl", "v")
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_injection.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/livesttt/injection/ tests/test_injection.py
git commit -m "feat: add injection/injector.py with clipboard paste"
```

---

### Task 9: injection/exporter.py

**Files:**
- Create: `src/livesttt/injection/exporter.py`
- Extend: `tests/test_injection.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_injection.py`:
```python
from pathlib import Path
from livesttt.injection import exporter


def test_save_transcript_creates_txt_next_to_source(tmp_path):
    audio = tmp_path / "meeting.wav"
    audio.touch()
    out = exporter.save_transcript("hello world", audio)
    assert out == tmp_path / "meeting.txt"
    assert out.read_text(encoding="utf-8") == "hello world"


def test_save_transcript_returns_output_path(tmp_path):
    audio = tmp_path / "clip.mp3"
    audio.touch()
    result = exporter.save_transcript("transcript text", audio)
    assert isinstance(result, Path)
    assert result.suffix == ".txt"


def test_save_transcript_overwrites_existing(tmp_path):
    audio = tmp_path / "clip.wav"
    audio.touch()
    exporter.save_transcript("first", audio)
    exporter.save_transcript("second", audio)
    assert (tmp_path / "clip.txt").read_text(encoding="utf-8") == "second"
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_injection.py -k "exporter or save_transcript" -v
```

Expected: 3 errors - `cannot import name 'exporter'`

- [ ] **Step 3: Implement exporter.py**

`src/livesttt/injection/exporter.py`:
```python
from pathlib import Path


def save_transcript(text: str, source_path: Path) -> Path:
    out = source_path.with_suffix(".txt")
    out.write_text(text, encoding="utf-8")
    return out
```

- [ ] **Step 4: Run all injection tests**

```bash
pytest tests/test_injection.py -v
```

Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add src/livesttt/injection/exporter.py tests/test_injection.py
git commit -m "feat: add injection/exporter.py to save transcript alongside audio file"
```

---

### Task 10: hotkeys/daemon.py

**Files:**
- Create: `src/livesttt/hotkeys/__init__.py`
- Create: `src/livesttt/hotkeys/daemon.py`
- Create: `tests/test_hotkeys.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_hotkeys.py`:
```python
from unittest.mock import patch, MagicMock, call
from livesttt.hotkeys import daemon


def test_register_calls_keyboard_add_hotkey():
    cb = MagicMock()
    with patch("keyboard.add_hotkey") as mock_add:
        daemon.register("ctrl+shift+space", cb)
    mock_add.assert_called_once_with("ctrl+shift+space", cb)


def test_register_ptt_hooks_press_and_release():
    on_press = MagicMock()
    on_release = MagicMock()
    with patch("keyboard.on_press_key") as mock_press, \
         patch("keyboard.on_release_key") as mock_release:
        daemon.register_ptt("f9", on_press, on_release)
    assert mock_press.call_count == 1
    assert mock_release.call_count == 1


def test_stop_unhooks_all():
    with patch("keyboard.unhook_all") as mock_unhook:
        daemon.stop()
    mock_unhook.assert_called_once()
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_hotkeys.py -v
```

Expected: 3 errors - `cannot import name 'daemon'`

- [ ] **Step 3: Implement daemon.py**

`src/livesttt/hotkeys/__init__.py`: empty file.

`src/livesttt/hotkeys/daemon.py`:
```python
from typing import Callable
import keyboard


def register(hotkey: str, callback: Callable[[], None]) -> None:
    keyboard.add_hotkey(hotkey, callback)


def register_ptt(
    key: str,
    on_press: Callable[[], None],
    on_release: Callable[[], None],
) -> None:
    keyboard.on_press_key(key, lambda _: on_press(), suppress=True)
    keyboard.on_release_key(key, lambda _: on_release(), suppress=True)


def stop() -> None:
    keyboard.unhook_all()
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_hotkeys.py -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/livesttt/hotkeys/ tests/test_hotkeys.py
git commit -m "feat: add hotkeys/daemon.py with PTT and toggle registration"
```

---

### Task 11: ui/tray.py and ui/settings.py

**Files:**
- Create: `src/livesttt/ui/__init__.py`
- Create: `src/livesttt/ui/tray.py`
- Create: `src/livesttt/ui/settings.py`

These modules drive the GUI event loop and are not unit-tested; they are verified manually at the end of Task 12.

- [ ] **Step 1: Create ui/__init__.py**

`src/livesttt/ui/__init__.py`: empty file.

- [ ] **Step 2: Create tray.py**

`src/livesttt/ui/tray.py`:
```python
from __future__ import annotations
import threading
import tkinter
from typing import Callable
import pystray
from PIL import Image, ImageDraw

_icon: pystray.Icon | None = None
_status = "idle"
_STATUS_COLORS = {"idle": "green", "recording": "red", "processing": "orange"}


def _make_icon(color: str) -> Image.Image:
    img = Image.new("RGB", (64, 64), color="black")
    draw = ImageDraw.Draw(img)
    draw.ellipse([8, 8, 56, 56], fill=color)
    return img


def set_status(status: str) -> None:
    global _status
    _status = status
    if _icon:
        _icon.icon = _make_icon(_STATUS_COLORS.get(status, "gray"))


def run(
    cfg,
    on_transcribe_file: Callable[[], None],
    on_open_settings: Callable[[], None],
    on_quit: Callable[[], None],
) -> None:
    global _icon

    menu = pystray.Menu(
        pystray.MenuItem("Transcribe file...", lambda icon, item: on_transcribe_file()),
        pystray.MenuItem("Settings", lambda icon, item: on_open_settings()),
        pystray.MenuItem("Quit", lambda icon, item: on_quit()),
    )
    _icon = pystray.Icon("livesttt", _make_icon("green"), "live-stt", menu)
    _icon.run()
```

- [ ] **Step 3: Create settings.py**

`src/livesttt/ui/settings.py`:
```python
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Callable
from livesttt.config import Config


def open_settings(cfg: Config, on_save: Callable[[Config], None]) -> None:
    win = tk.Tk()
    win.title("live-stt settings")
    win.resizable(False, False)

    tk.Label(win, text="Hotkey:").grid(row=0, column=0, padx=8, pady=4, sticky="w")
    hotkey_var = tk.StringVar(value=cfg.hotkey)
    tk.Entry(win, textvariable=hotkey_var, width=24).grid(row=0, column=1, padx=8)

    tk.Label(win, text="Model:").grid(row=1, column=0, padx=8, pady=4, sticky="w")
    model_var = tk.StringVar(value=cfg.model)
    tk.Entry(win, textvariable=model_var, width=24).grid(row=1, column=1, padx=8)

    refine_var = tk.BooleanVar(value=cfg.refine)
    tk.Checkbutton(win, text="Refine with LLM", variable=refine_var).grid(
        row=2, column=0, columnspan=2, padx=8, pady=4, sticky="w"
    )

    def _save():
        updated = Config(
            hotkey=hotkey_var.get().strip(),
            model=model_var.get().strip(),
            refine=refine_var.get(),
            vad_threshold=cfg.vad_threshold,
        )
        on_save(updated)
        win.destroy()

    tk.Button(win, text="Save", command=_save).grid(
        row=3, column=0, columnspan=2, pady=8
    )
    win.mainloop()
```

- [ ] **Step 4: Commit**

```bash
git add src/livesttt/ui/
git commit -m "feat: add ui/tray.py and ui/settings.py stubs"
```

---

### Task 12: Wire __main__.py and smoke test

**Files:**
- Modify: `src/livesttt/__main__.py`

- [ ] **Step 1: Implement __main__.py**

`src/livesttt/__main__.py`:
```python
from __future__ import annotations
import threading
import tkinter.filedialog

from livesttt import config as cfg_module
from livesttt.audio import capture, vad, reader
from livesttt.stt import engine as stt_engine
from livesttt.llm import client as llm_client
from livesttt.injection import injector, exporter
from livesttt.hotkeys import daemon as hotkey_daemon
from livesttt.ui import tray, settings

_cfg = cfg_module.Config()
_stop_event = threading.Event()


def _on_ptt_press() -> None:
    _stop_event.clear()
    tray.set_status("recording")
    thread = threading.Thread(target=_capture_and_process, daemon=True)
    thread.start()


def _on_ptt_release() -> None:
    _stop_event.set()


def _capture_and_process() -> None:
    audio = capture.start_recording(_stop_event)
    tray.set_status("processing")
    audio = vad.trim_silence(audio, threshold=_cfg.vad_threshold)
    if not audio:
        tray.set_status("idle")
        return
    text = stt_engine.transcribe(audio)
    if _cfg.refine:
        text = llm_client.refine(text, "clean_up", _cfg.model)
    injector.inject(text)
    tray.set_status("idle")


def _on_transcribe_file() -> None:
    path_str = tkinter.filedialog.askopenfilename(
        title="Select audio file",
        filetypes=[("Audio files", "*.wav *.mp3 *.m4a *.flac"), ("All files", "*.*")],
    )
    if not path_str:
        return
    from pathlib import Path
    path = Path(path_str)
    tray.set_status("processing")
    audio = reader.read_file(path)
    text = stt_engine.transcribe(audio)
    if _cfg.refine:
        text = llm_client.refine(text, "clean_up", _cfg.model)
    injector.inject(text)
    exporter.save_transcript(text, path)
    tray.set_status("idle")


def _on_open_settings() -> None:
    def _save(updated_cfg):
        global _cfg
        _cfg = updated_cfg
        cfg_module.save(updated_cfg)

    settings.open_settings(_cfg, on_save=_save)


def _on_quit() -> None:
    hotkey_daemon.stop()
    tray._icon.stop() if tray._icon else None


def main() -> None:
    global _cfg
    _cfg = cfg_module.load()

    # Wire up VibeVoice here once the library is available:
    # from vibeVoice import transcribe as vv_transcribe
    # stt_engine.set_backend(vv_transcribe)

    hotkey_daemon.register_ptt(
        _cfg.hotkey.split("+")[-1],
        on_press=_on_ptt_press,
        on_release=_on_ptt_release,
    )

    tray.run(
        cfg=_cfg,
        on_transcribe_file=_on_transcribe_file,
        on_open_settings=_on_open_settings,
        on_quit=_on_quit,
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the full test suite**

```bash
pytest tests/ -v
```

Expected: all tests pass (tray and settings are not unit-tested)

- [ ] **Step 3: Verify entry point installs cleanly**

```bash
pip install -e ".[dev]"
python -c "from livesttt.__main__ import main; print('import ok')"
```

Expected: `import ok`

- [ ] **Step 4: Manual smoke test (with VibeVoice stub)**

Since VibeVoice is not yet wired, test the tray launch with a dummy backend:

```bash
python -c "
from livesttt.stt import engine
engine.set_backend(lambda audio: 'test transcript')
from livesttt.__main__ import main
main()
"
```

Expected: tray icon appears in the system tray. Right-click shows menu with 'Transcribe file...', 'Settings', 'Quit'. Quit exits cleanly.

- [ ] **Step 5: Final commit**

```bash
git add src/livesttt/__main__.py
git commit -m "feat: wire all subsystems in __main__.py"
```

- [ ] **Step 6: Push**

```bash
git push origin master
```

---

## Self-Review Notes

- Spec requirement "Transcribe file..." flow (steps 1-7): covered in `_on_transcribe_file` in Task 12 and `reader.py` (Task 5), `exporter.py` (Task 9).
- Spec requirement "tray status indicator": `set_status()` in `tray.py` (Task 11), called from `__main__.py` (Task 12).
- Spec requirement `config.py` load/save: Task 3, tested with 4 cases.
- Spec requirement injectable STT backend: Task 6 `set_backend()`.
- VibeVoice wiring left as a clearly marked stub comment in `__main__.py` and `engine.py` - intentional, API not yet known.
- `livesttt.spec` (PyInstaller) omitted - spec says "generated later", not part of this scaffold plan.
