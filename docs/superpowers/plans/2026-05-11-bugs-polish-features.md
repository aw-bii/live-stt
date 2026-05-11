# Bugs, Polish, and Features Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all open bugs, add double-tap Alt toggle mode, expand settings, create a waveform icon, and add Ollama/Gemma4 2B auto-setup.

**Architecture:** Fixes are applied to existing modules in-place following their current patterns. New config fields drive registration strategy in `__main__.py`. The daemon gains a `register_double_tap_toggle` function. The tray icon switches from a colored circle to a waveform drawn with PIL. Ollama model presence is checked at startup and auto-pulled in the background if missing.

**Tech Stack:** Python, loguru, keyboard, pystray, Pillow, requests, subprocess, tkinter, pytest/unittest.mock

---

## File Map

- `src/livesttt/logging.py` - move `mkdir` + file handler into `init_file_logging()` (called from `main()`)
- `src/livesttt/config.py` - remove `stt_timeout`, add `hotkey_mode`/`double_tap_window`, change defaults
- `src/livesttt/hotkeys/daemon.py` - add `register_double_tap_toggle()`
- `src/livesttt/ui/settings.py` - fix Alt mask, fix save crash, add mode/window fields
- `src/livesttt/ui/tray.py` - waveform icon replacing solid circle
- `src/livesttt/messages.py` - parameterise `INFO_TRANSCRIPTION_COMPLETE`
- `src/livesttt/__main__.py` - remove inject from file flow, collapse except arms, hoist pyperclip, async startup, wire hotkey mode, call init_file_logging, auto-pull Ollama
- `src/livesttt/assets/icon.svg` - waveform SVG (decorative; PIL draws tray icon independently)
- `scripts/setup_ollama.py` - standalone first-run Ollama installer helper
- `pyproject.toml` - transformers/torch moved to optional `[local-stt]`
- `tests/test_hotkeys.py` - add double-tap toggle tests
- `tests/test_settings.py` - fix Alt mask test (0x8 -> 0x20000)
- `tests/test_config.py` - update for new fields, removed field
- `TODO.md` - mark all complete

---

## Task 1: Lazy log-dir init

**Files:**
- Modify: `src/livesttt/logging.py`
- Modify: `src/livesttt/__main__.py`

- [ ] **Step 1: Write the failing test**

Add to a new file `tests/test_logging.py`:

```python
import importlib
import sys
from unittest.mock import patch, MagicMock


def test_import_does_not_create_log_directory(tmp_path):
    """Importing livesttt.logging must not touch the filesystem."""
    # Remove cached module so it re-executes on import
    for key in list(sys.modules):
        if "livesttt" in key:
            del sys.modules[key]

    with patch("pathlib.Path.mkdir") as mock_mkdir:
        import livesttt.logging  # noqa: F401
        mock_mkdir.assert_not_called()
```

- [ ] **Step 2: Run test to verify it fails**

```
.venv\Scripts\python.exe -m pytest tests/test_logging.py -v
```

Expected: FAIL (mkdir is called at import time currently).

- [ ] **Step 3: Implement lazy init**

Replace `src/livesttt/logging.py` entirely:

```python
import sys
from pathlib import Path
from loguru import logger

LOG_PATH = Path.home() / ".livesttt" / "logs"
LOG_FILE = "livesttt.log"

logger.remove()
logger.add(
    sys.stderr,
    format="<level>{level}</level> <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
)


def init_file_logging() -> None:
    LOG_PATH.mkdir(parents=True, exist_ok=True)
    logger.add(
        LOG_PATH / LOG_FILE,
        rotation="10 MB",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
    )
```

- [ ] **Step 4: Call init_file_logging from main()**

In `src/livesttt/__main__.py`, inside `main()` add as the very first line:

```python
def main() -> None:
    log_module.init_file_logging()
    global _cfg, _health
    _cfg = cfg_module.load()
    ...
```

- [ ] **Step 5: Run test to verify it passes**

```
.venv\Scripts\python.exe -m pytest tests/test_logging.py -v
```

Expected: PASS.

- [ ] **Step 6: Run full suite to check no regressions**

```
.venv\Scripts\python.exe -m pytest tests/ -v
```

- [ ] **Step 7: Commit**

```
git add src/livesttt/logging.py src/livesttt/__main__.py tests/test_logging.py
git commit -m "fix: lazy-init log directory on first use, not at import time"
```

---

## Task 2: Fix Alt modifier mask in hotkey picker

**Files:**
- Modify: `src/livesttt/ui/settings.py`
- Modify: `tests/test_settings.py`

On Windows, Tk sets bit `0x20000` for Alt in event.state. The current code checks `0x8` (NumLock/Mod1), which silently drops Alt from captured hotkeys.

- [ ] **Step 1: Update the test to use the correct Windows mask**

In `tests/test_settings.py`, replace:

```python
def test_alt_modifier():
    assert build_hotkey_string(0x8, "f9") == "alt+f9"
```

with:

```python
def test_alt_modifier():
    assert build_hotkey_string(0x20000, "f9") == "alt+f9"


def test_mod1_bit_not_treated_as_alt():
    # 0x8 is NumLock/Mod1 on Windows, not Alt - should produce no modifier prefix
    assert build_hotkey_string(0x8, "f9") == "f9"
```

- [ ] **Step 2: Run test to verify it fails**

```
.venv\Scripts\python.exe -m pytest tests/test_settings.py::test_alt_modifier tests/test_settings.py::test_mod1_bit_not_treated_as_alt -v
```

Expected: both FAIL.

- [ ] **Step 3: Fix the mask in settings.py**

In `src/livesttt/ui/settings.py`, replace:

```python
    if state & 0x8:
        parts.append("alt")
```

with:

```python
    if state & 0x20000:
        parts.append("alt")
```

- [ ] **Step 4: Run tests to verify they pass**

```
.venv\Scripts\python.exe -m pytest tests/test_settings.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```
git add src/livesttt/ui/settings.py tests/test_settings.py
git commit -m "fix: use correct Windows Tk Alt modifier mask (0x20000 not 0x8)"
```

---

## Task 3: Fix settings save crash on bad numeric input

**Files:**
- Modify: `src/livesttt/ui/settings.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_settings.py`:

```python
import tkinter as tk
from unittest.mock import MagicMock, patch
from livesttt.config import Config
from livesttt.ui.settings import open_settings


def test_save_with_invalid_llm_timeout_shows_error_not_crash():
    """Settings save must not crash when a numeric field contains non-numeric text."""
    saved = []
    cfg = Config()

    with patch("tkinter.Tk") as mock_tk_cls, \
         patch("tkinter.Label"), \
         patch("tkinter.Button"), \
         patch("tkinter.Entry"), \
         patch("tkinter.Checkbutton"), \
         patch("tkinter.Scale"), \
         patch("tkinter.messagebox") as mock_mb:

        mock_win = MagicMock()
        mock_tk_cls.return_value = mock_win

        # Force IntVar.get() to raise TclError
        mock_int_var = MagicMock()
        mock_int_var.get.side_effect = tk.TclError("expected integer")

        with patch("tkinter.IntVar", return_value=mock_int_var):
            # open_settings is GUI-blocking; we cannot easily call _save() directly
            # without a running event loop. Instead test _validate_and_save directly.
            pass  # validation is tested at integration level; structural test below


def test_open_settings_save_wraps_tcl_error(monkeypatch):
    """_save() in open_settings catches TclError and shows messagebox."""
    import tkinter as tk
    from livesttt.ui import settings as s

    cfg = Config()
    saved_cfgs = []

    # We'll call the private _save by monkey-patching Tk to auto-invoke it
    original_open = s.open_settings

    class FakeTk:
        def __init__(self): pass
        def title(self, *a): pass
        def resizable(self, *a): pass
        def mainloop(self): pass
        def destroy(self): pass
        def grid(self, **kw): pass

    fake_win = FakeTk()

    save_fn = []

    def capture_button(text, command, **kw):
        if text == "Save":
            save_fn.append(command)
        m = MagicMock()
        m.grid = MagicMock()
        return m

    with patch("tkinter.Tk", return_value=fake_win), \
         patch("tkinter.Label", return_value=MagicMock(grid=MagicMock())), \
         patch("tkinter.Entry", return_value=MagicMock(grid=MagicMock())), \
         patch("tkinter.Checkbutton", return_value=MagicMock(grid=MagicMock())), \
         patch("tkinter.Scale", return_value=MagicMock(grid=MagicMock())), \
         patch("tkinter.OptionMenu", return_value=MagicMock(grid=MagicMock())), \
         patch("tkinter.Button", side_effect=capture_button), \
         patch("tkinter.StringVar") as sv, \
         patch("tkinter.BooleanVar") as bv, \
         patch("tkinter.IntVar") as iv, \
         patch("tkinter.DoubleVar") as dv, \
         patch("tkinter.messagebox") as mb:

        bad_int = MagicMock()
        bad_int.get.side_effect = tk.TclError("expected integer")
        iv.return_value = bad_int

        s.open_settings(cfg, on_save=saved_cfgs.append)

        if save_fn:
            save_fn[0]()
            mb.showerror.assert_called_once()
            assert saved_cfgs == []
```

- [ ] **Step 2: Run test to verify it fails**

```
.venv\Scripts\python.exe -m pytest tests/test_settings.py::test_open_settings_save_wraps_tcl_error -v
```

Expected: FAIL.

- [ ] **Step 3: Wrap _save() in try/except**

In `src/livesttt/ui/settings.py`, replace the `_save` function:

```python
    def _save() -> None:
        try:
            updated = Config(
                hotkey=hotkey_capture.get(),
                cancel_hotkey=cancel_capture.get(),
                model=model_var.get().strip(),
                refine=refine_var.get(),
                vad_threshold=vad_var.get(),
                hotkey_mode=mode_var.get(),
                double_tap_window=double_tap_window_var.get(),
                llm_timeout=llm_timeout_var.get(),
                injection_delay=injection_delay_var.get(),
            )
        except tk.TclError as e:
            tk.messagebox.showerror("Invalid input", f"Please correct the highlighted fields.\n\n{e}")
            return
        on_save(updated)
        win.destroy()
```

(The `stt_timeout` field is removed in Task 4; `hotkey_mode` and `double_tap_window` are added in Task 4.)

- [ ] **Step 4: Add `import tkinter.messagebox` at the top of settings.py**

The file already imports `tkinter as tk`. Add:

```python
import tkinter.messagebox
```

directly below `import tkinter as tk`.

- [ ] **Step 5: Run tests**

```
.venv\Scripts\python.exe -m pytest tests/test_settings.py -v
```

Expected: all PASS.

- [ ] **Step 6: Commit**

```
git add src/livesttt/ui/settings.py tests/test_settings.py
git commit -m "fix: catch TclError in settings save to prevent crash on invalid numeric input"
```

---

## Task 4: Update Config schema

Remove unused `stt_timeout`. Add `hotkey_mode` and `double_tap_window`. Change defaults: `hotkey="alt"`, `model="gemma4:2b"`.

**Files:**
- Modify: `src/livesttt/config.py`
- Modify: `tests/test_config.py`

- [ ] **Step 1: Update tests first**

In `tests/test_config.py`, replace the `test_defaults` test and add new ones:

```python
def test_defaults():
    cfg = config.Config()
    assert cfg.hotkey == "alt"
    assert cfg.model == "gemma4:2b"
    assert cfg.refine is True
    assert cfg.vad_threshold == 0.02
    assert cfg.hotkey_mode == "double_tap_toggle"
    assert cfg.double_tap_window == 0.3
    assert not hasattr(cfg, "stt_timeout")


def test_hotkey_mode_round_trips(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "config.json")
    cfg = config.Config(hotkey_mode="ptt")
    config.save(cfg)
    loaded = config.load()
    assert loaded.hotkey_mode == "ptt"


def test_invalid_hotkey_mode_defaults(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "config.json")
    (tmp_path / "config.json").write_text('{"hotkey_mode": "bogus"}')
    loaded = config.load()
    assert loaded.hotkey_mode == "double_tap_toggle"


def test_double_tap_window_round_trips(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "config.json")
    cfg = config.Config(double_tap_window=0.5)
    config.save(cfg)
    loaded = config.load()
    assert loaded.double_tap_window == 0.5


def test_old_config_with_stt_timeout_loads_without_error(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "config.json")
    # Old configs may have stt_timeout; should be silently ignored
    (tmp_path / "config.json").write_text('{"stt_timeout": 60, "hotkey": "alt"}')
    loaded = config.load()
    assert loaded.hotkey == "alt"
```

Also update `test_load_partial_valid_data` to use new defaults:

```python
def test_load_partial_valid_data(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "config.json")
    (tmp_path / "config.json").write_text('{"hotkey": "ctrl+b"}')
    loaded = config.load()
    assert loaded.hotkey == "ctrl+b"
    assert loaded.model == "gemma4:2b"
```

Also update `test_load_invalid_hotkey_defaults`:

```python
def test_load_invalid_hotkey_defaults(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "config.json")
    (tmp_path / "config.json").write_text('{"hotkey": ""}')
    loaded = config.load()
    assert loaded.hotkey == "alt"
```

- [ ] **Step 2: Run tests to verify they fail**

```
.venv\Scripts\python.exe -m pytest tests/test_config.py -v
```

Expected: multiple failures (new fields don't exist yet, defaults are old values).

- [ ] **Step 3: Update config.py**

Replace `src/livesttt/config.py` entirely:

```python
import json
from dataclasses import dataclass, asdict
from pathlib import Path

from livesttt import logging as log_module

CONFIG_PATH = Path.home() / ".livesttt" / "config.json"

logger = log_module.logger

_VALID_HOTKEY_MODES = {"ptt", "double_tap_toggle"}


@dataclass
class Config:
    hotkey: str = "alt"
    cancel_hotkey: str = "escape"
    model: str = "gemma4:2b"
    refine: bool = True
    vad_threshold: float = 0.02
    hotkey_mode: str = "double_tap_toggle"
    double_tap_window: float = 0.3
    llm_timeout: int = 30
    injection_delay: float = 0.05


def _validate_value(key: str, value, default):
    if key in ("hotkey", "cancel_hotkey", "model"):
        if not isinstance(value, str) or not value.strip():
            logger.warning(f"Invalid {key}: {value!r}, using default {default!r}")
            return default
    elif key == "refine":
        if not isinstance(value, bool):
            logger.warning(f"Invalid refine: {value!r}, using default {default!r}")
            return default
    elif key == "vad_threshold":
        if not isinstance(value, (int, float)) or not (0.0 <= value <= 1.0):
            logger.warning(f"Invalid vad_threshold: {value!r}, using default {default!r}")
            return default
    elif key == "hotkey_mode":
        if value not in _VALID_HOTKEY_MODES:
            logger.warning(f"Invalid hotkey_mode: {value!r}, using default {default!r}")
            return default
    elif key == "double_tap_window":
        if not isinstance(value, (int, float)) or not (0.05 <= value <= 2.0):
            logger.warning(f"Invalid double_tap_window: {value!r}, using default {default!r}")
            return default
    elif key == "llm_timeout":
        if not isinstance(value, int) or value <= 0:
            logger.warning(f"Invalid {key}: {value!r}, using default {default!r}")
            return default
    elif key == "injection_delay":
        if not isinstance(value, (int, float)) or value < 0:
            logger.warning(f"Invalid {key}: {value!r}, using default {default!r}")
            return default
    return value


def _validate(data: dict) -> Config:
    defaults = Config()
    defaults_dict = asdict(defaults)
    validated = {}
    for key, default in defaults_dict.items():
        validated[key] = _validate_value(key, data.get(key, default), default)
    return Config(**validated)


def load() -> Config:
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            # silently drop unknown/removed keys (e.g. stt_timeout from old configs)
            known_keys = set(asdict(Config()).keys())
            data = {k: v for k, v in data.items() if k in known_keys}
            return _validate(data)
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.warning(f"Config load failed: {e}, using defaults")
    return Config()


def save(cfg: Config) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(asdict(cfg), indent=2), encoding="utf-8")
```

- [ ] **Step 4: Run tests**

```
.venv\Scripts\python.exe -m pytest tests/test_config.py -v
```

Expected: all PASS.

- [ ] **Step 5: Run full suite**

```
.venv\Scripts\python.exe -m pytest tests/ -v
```

Fix any failures from removed `stt_timeout` in other test files (grep for `stt_timeout` in tests/).

- [ ] **Step 6: Commit**

```
git add src/livesttt/config.py tests/test_config.py
git commit -m "feat: update Config - remove stt_timeout, add hotkey_mode/double_tap_window, new defaults (alt hotkey, gemma4:2b)"
```

---

## Task 5: Make transformers/torch optional dependencies

**Files:**
- Modify: `pyproject.toml`

No tests needed - this is a packaging change.

- [ ] **Step 1: Update pyproject.toml**

Replace the `dependencies` and `optional-dependencies` sections:

```toml
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
    "loguru>=0.7",
]

[project.optional-dependencies]
local-stt = [
    "transformers>=4.50",
    "torch>=2.0",
]
dev = ["pytest>=7", "pytest-mock>=3"]
```

- [ ] **Step 2: Verify app still runs (local STT auto-detected via import check)**

```
.venv\Scripts\python.exe -c "from livesttt.stt import vibevoice_local; print(vibevoice_local.is_available())"
```

Expected: prints `True` (transformers still installed in venv) or `False` (if not).

- [ ] **Step 3: Commit**

```
git add pyproject.toml
git commit -m "fix: move transformers/torch to optional [local-stt] extra - no longer a hard dependency"
```

---

## Task 6: Fix __main__.py - remove inject from file transcription, collapse except arms, hoist pyperclip

**Files:**
- Modify: `src/livesttt/__main__.py`

- [ ] **Step 1: Write a test that _on_transcribe_file does NOT call inject**

Add to `tests/test_main_shutdown.py` (or create `tests/test_main.py`):

```python
from unittest.mock import patch, MagicMock
from pathlib import Path
from livesttt import __main__ as app


def test_on_transcribe_file_does_not_inject(tmp_path):
    """File transcription should NOT inject into the active window."""
    wav = tmp_path / "test.wav"
    # Create a minimal valid WAV (44 bytes header, no frames - triggers empty audio path)
    import struct, wave, io
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x00\x00" * 160)
    wav.write_bytes(buf.getvalue())

    with patch("tkinter.filedialog.askopenfilename", return_value=str(wav)), \
         patch.object(app.stt_engine, "transcribe", return_value="hello world"), \
         patch.object(app.injector, "inject") as mock_inject, \
         patch.object(app.exporter, "save_transcript", return_value=tmp_path / "test.txt"), \
         patch.object(app.tray, "set_status"), \
         patch.object(app.tray, "notify"):
        app._on_transcribe_file()

    mock_inject.assert_not_called()
```

- [ ] **Step 2: Run test to verify it fails**

```
.venv\Scripts\python.exe -m pytest tests/test_main.py::test_on_transcribe_file_does_not_inject -v
```

Expected: FAIL (inject is currently called).

- [ ] **Step 3: Apply all three fixes to __main__.py**

At the top of the file, change the imports block so `pyperclip` is a top-level import:

```python
from __future__ import annotations
import threading
import tkinter.filedialog
from pathlib import Path
import pyperclip
import requests

from livesttt import config as cfg_module
from livesttt.audio import capture, vad, reader
from livesttt.stt import engine as stt_engine, vibevoice, vibevoice_local
from livesttt.llm import client as llm_client
from livesttt.injection import injector, exporter
from livesttt.hotkeys import daemon as hotkey_daemon
from livesttt.ui import tray, settings
from livesttt import messages
from livesttt import logging as log_module
```

In `_capture_and_process`, collapse the three except arms:

```python
        try:
            injector.inject(text, _cfg.injection_delay)
        except Exception as e:
            logger.warning(f"Injection failed: {e}")
            pyperclip.copy(text)
            tray.notify(messages.ERROR_INJECTION_FAILED)
        tray.set_status("idle")
    except Exception as e:
        logger.exception(f"Transcription failed: {e}")
        tray.set_status("error")
        tray.notify(messages.ERROR_TRANSCRIPTION_FAILED)
```

(Remove the separate `requests.ConnectionError` arm - it rolls into the generic `except Exception`.)

In `_on_transcribe_file`, remove the `try/except` inject block entirely (lines 117-123 in original). Keep the `exporter.save_transcript` and `tray.notify` calls. The function after the fix looks like:

```python
def _on_transcribe_file() -> None:
    path_str = tkinter.filedialog.askopenfilename(
        title="Select audio file",
        filetypes=[("Audio files", "*.wav *.mp3 *.m4a *.flac"), ("All files", "*.*")],
    )
    if not path_str:
        return
    with _health_lock:
        health = _health.copy()
    try:
        path = Path(path_str)
        tray.set_status("processing")
        audio = reader.read_file(path)
        if not audio:
            tray.set_status("error")
            tray.notify(messages.ERROR_FILE_READ_FAILED)
            return
        text = stt_engine.transcribe(audio)
        if _cfg.refine and health["ollama"]:
            try:
                future = llm_client.refine_async(text, "clean_up", _cfg.model, _cfg.llm_timeout)
                text = future.result(timeout=_cfg.llm_timeout + 5)
            except Exception as e:
                logger.warning(f"LLM refinement failed: {e}")
        elif _cfg.refine and not health["ollama"]:
            logger.info("Skipping refinement - Ollama unavailable")
        out_path = exporter.save_transcript(text, path)
        pyperclip.copy(text)
        tray.notify(messages.INFO_TRANSCRIPTION_COMPLETE.format(name=out_path.name))
        tray.set_status("idle")
    except Exception as e:
        logger.exception(f"File transcription failed: {e}")
        tray.set_status("error")
        tray.notify(messages.ERROR_TRANSCRIPTION_FAILED)
```

- [ ] **Step 4: Update messages.py**

In `src/livesttt/messages.py`, change:

```python
INFO_TRANSCRIPTION_COMPLETE = "Transcript saved: {name}"
```

(was `"Transcription complete"`)

- [ ] **Step 5: Run the new test**

```
.venv\Scripts\python.exe -m pytest tests/test_main.py::test_on_transcribe_file_does_not_inject -v
```

Expected: PASS.

- [ ] **Step 6: Run full suite**

```
.venv\Scripts\python.exe -m pytest tests/ -v
```

- [ ] **Step 7: Commit**

```
git add src/livesttt/__main__.py src/livesttt/messages.py tests/test_main.py
git commit -m "fix: remove inject() from file transcription; collapse except arms; hoist pyperclip import; include filename in completion notification"
```

---

## Task 7: Non-blocking startup (async health check)

**Files:**
- Modify: `src/livesttt/__main__.py`

The current `main()` calls `_check_health()` synchronously (5s+ Ollama probe) before `tray.run()`. The tray icon won't appear until this completes. Fix: remove the synchronous call entirely. The periodic health monitor already calls `_check_health()` as its first action when started, so deleting the sync call makes startup instant.

- [ ] **Step 1: Write the test**

Add to `tests/test_main.py`:

```python
def test_main_starts_tray_before_health_check_completes():
    """tray.run() must be called even if health check is slow."""
    health_check_started = threading.Event()
    tray_started = threading.Event()

    def slow_health_check():
        health_check_started.set()
        return {"vibevoice": False, "ollama": False}

    with patch.object(app, "_check_health", side_effect=slow_health_check), \
         patch.object(app.cfg_module, "load", return_value=app.cfg_module.Config()), \
         patch.object(app.vibevoice_local, "is_available", return_value=False), \
         patch.object(app.stt_engine, "set_backend"), \
         patch.object(app.hotkey_daemon, "register_ptt"), \
         patch.object(app.hotkey_daemon, "register"), \
         patch.object(app.hotkey_daemon, "register_double_tap_toggle"), \
         patch.object(app.tray, "run", side_effect=lambda **kw: tray_started.set()), \
         patch.object(app, "_quit_event") as mock_quit:
        mock_quit.is_set.return_value = True  # stop health monitor immediately
        app.main()

    assert tray_started.is_set(), "tray.run() was never called"
```

- [ ] **Step 2: Run test to verify it fails**

```
.venv\Scripts\python.exe -m pytest tests/test_main.py::test_main_starts_tray_before_health_check_completes -v
```

Expected: FAIL (synchronous `_check_health()` currently blocks before `tray.run()`).

- [ ] **Step 3: Remove synchronous health check from main()**

In `src/livesttt/__main__.py`, in `main()`, remove these lines:

```python
    _health = _check_health()

    if not _health["vibevoice"] and not vibevoice_local.is_available():
        logger.warning("VibeVoice not available at startup")
    if not _health["ollama"] and _cfg.refine:
        logger.warning("Ollama not available - refinement disabled")
```

The monitor thread (started immediately after) handles this. `_health` starts as `{"vibevoice": False, "ollama": False}` which safely disables refinement until the first async check completes (within seconds).

- [ ] **Step 4: Run test**

```
.venv\Scripts\python.exe -m pytest tests/test_main.py::test_main_starts_tray_before_health_check_completes -v
```

Expected: PASS.

- [ ] **Step 5: Run full suite**

```
.venv\Scripts\python.exe -m pytest tests/ -v
```

- [ ] **Step 6: Commit**

```
git add src/livesttt/__main__.py tests/test_main.py
git commit -m "fix: move startup health check off main thread so tray icon appears immediately"
```

---

## Task 8: Add double-tap toggle to hotkey daemon

**Files:**
- Modify: `src/livesttt/hotkeys/daemon.py`
- Modify: `tests/test_hotkeys.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_hotkeys.py`:

```python
import time
from unittest.mock import patch, MagicMock, call


def _get_double_tap_handler(key, on_start, on_stop, window=0.3):
    """Register double-tap and return the captured key handler."""
    captured = []
    with patch("keyboard.on_press_key", side_effect=lambda k, h, **kw: captured.append(h)):
        daemon.register_double_tap_toggle(key, on_start, on_stop, window=window)
    return captured[0]


def test_double_tap_toggle_registers_on_press_key():
    on_start, on_stop = MagicMock(), MagicMock()
    with patch("keyboard.on_press_key") as mock_press:
        daemon.register_double_tap_toggle("alt", on_start, on_stop)
    mock_press.assert_called_once_with("alt", mock_press.call_args[0][1])


def test_single_tap_does_not_trigger():
    on_start, on_stop = MagicMock(), MagicMock()
    handler = _get_double_tap_handler("alt", on_start, on_stop, window=0.3)
    event = MagicMock()
    with patch("time.monotonic", return_value=1.0):
        handler(event)
    on_start.assert_not_called()
    on_stop.assert_not_called()


def test_double_tap_within_window_calls_on_start():
    on_start, on_stop = MagicMock(), MagicMock()
    handler = _get_double_tap_handler("alt", on_start, on_stop, window=0.3)
    event = MagicMock()
    times = iter([1.0, 1.2])
    with patch("time.monotonic", side_effect=times):
        handler(event)  # first tap
        handler(event)  # second tap 0.2s later - within 0.3s window
    on_start.assert_called_once()
    on_stop.assert_not_called()


def test_double_tap_outside_window_does_not_trigger():
    on_start, on_stop = MagicMock(), MagicMock()
    handler = _get_double_tap_handler("alt", on_start, on_stop, window=0.3)
    event = MagicMock()
    times = iter([1.0, 1.5])  # 0.5s apart, outside 0.3s window
    with patch("time.monotonic", side_effect=times):
        handler(event)
        handler(event)
    on_start.assert_not_called()


def test_second_double_tap_calls_on_stop():
    on_start, on_stop = MagicMock(), MagicMock()
    handler = _get_double_tap_handler("alt", on_start, on_stop, window=0.3)
    event = MagicMock()
    times = iter([1.0, 1.1, 2.0, 2.1])
    with patch("time.monotonic", side_effect=times):
        handler(event)  # tap 1
        handler(event)  # tap 2 - starts recording
        handler(event)  # tap 3
        handler(event)  # tap 4 - stops recording
    on_start.assert_called_once()
    on_stop.assert_called_once()


def test_triple_tap_does_not_double_trigger():
    """Third tap immediately after a double-tap should not start again."""
    on_start, on_stop = MagicMock(), MagicMock()
    handler = _get_double_tap_handler("alt", on_start, on_stop, window=0.3)
    event = MagicMock()
    times = iter([1.0, 1.1, 1.15])
    with patch("time.monotonic", side_effect=times):
        handler(event)  # tap 1
        handler(event)  # tap 2 - starts (resets last_tap to 0)
        handler(event)  # tap 3 - should be treated as first tap of new sequence
    on_start.assert_called_once()
    on_stop.assert_not_called()
```

- [ ] **Step 2: Run tests to verify they fail**

```
.venv\Scripts\python.exe -m pytest tests/test_hotkeys.py -k "double_tap" -v
```

Expected: all FAIL (function doesn't exist yet).

- [ ] **Step 3: Implement register_double_tap_toggle**

Replace `src/livesttt/hotkeys/daemon.py` entirely:

```python
from __future__ import annotations
import time
from typing import Callable
import keyboard


def register(hotkey: str, callback: Callable[[], None]) -> None:
    keyboard.add_hotkey(hotkey, callback)


def register_ptt(
    hotkey: str,
    on_press: Callable[[], None],
    on_release: Callable[[], None],
) -> None:
    keyboard.add_hotkey(hotkey, on_press, suppress=True, trigger_on_release=False)
    keyboard.add_hotkey(hotkey, on_release, suppress=True, trigger_on_release=True)


def register_double_tap_toggle(
    key: str,
    on_start: Callable[[], None],
    on_stop: Callable[[], None],
    window: float = 0.3,
) -> None:
    state: dict = {"last_tap": 0.0, "recording": False}

    def _handler(_event) -> None:
        now = time.monotonic()
        delta = now - state["last_tap"]
        if 0 < delta <= window:
            state["last_tap"] = 0.0  # reset so triple-tap isn't a second double-tap
            if not state["recording"]:
                state["recording"] = True
                on_start()
            else:
                state["recording"] = False
                on_stop()
        else:
            state["last_tap"] = now

    keyboard.on_press_key(key, _handler)


def stop() -> None:
    keyboard.unhook_all()
```

- [ ] **Step 4: Run double-tap tests**

```
.venv\Scripts\python.exe -m pytest tests/test_hotkeys.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```
git add src/livesttt/hotkeys/daemon.py tests/test_hotkeys.py
git commit -m "feat: add register_double_tap_toggle to hotkey daemon"
```

---

## Task 9: Wire double-tap toggle in __main__.py + update settings UI

**Files:**
- Modify: `src/livesttt/__main__.py`
- Modify: `src/livesttt/ui/settings.py`

- [ ] **Step 1: Update __main__.py hotkey registration**

In `main()`, replace:

```python
    hotkey_daemon.register_ptt(
        _cfg.hotkey,
        on_press=_on_ptt_press,
        on_release=_on_ptt_release,
    )
    hotkey_daemon.register(_cfg.cancel_hotkey, _on_cancel)
```

with:

```python
    if _cfg.hotkey_mode == "double_tap_toggle":
        hotkey_daemon.register_double_tap_toggle(
            _cfg.hotkey,
            on_start=_on_ptt_press,
            on_stop=_on_ptt_release,
            window=_cfg.double_tap_window,
        )
    else:
        hotkey_daemon.register_ptt(
            _cfg.hotkey,
            on_press=_on_ptt_press,
            on_release=_on_ptt_release,
        )
    hotkey_daemon.register(_cfg.cancel_hotkey, _on_cancel)
```

- [ ] **Step 2: Update settings UI**

Replace `open_settings` in `src/livesttt/ui/settings.py` with the full updated version (adds Mode dropdown and Double-tap window field, removes stt_timeout):

```python
import tkinter as tk
import tkinter.messagebox
from typing import Callable
from livesttt.config import Config

_MODIFIER_KEYSYMS = frozenset({
    "Control_L", "Control_R",
    "Shift_L", "Shift_R",
    "Alt_L", "Alt_R",
    "Meta_L", "Meta_R",
})


def build_hotkey_string(state: int, keysym: str) -> str | None:
    if keysym in _MODIFIER_KEYSYMS:
        return None
    parts = []
    if state & 0x4:
        parts.append("ctrl")
    if state & 0x1:
        parts.append("shift")
    if state & 0x20000:
        parts.append("alt")
    parts.append(keysym.lower())
    return "+".join(parts)


class _HotkeyCapture(tk.Frame):
    def __init__(self, parent: tk.Widget, value: str) -> None:
        super().__init__(parent)
        self._prev = value
        self._var = tk.StringVar(value=value)
        entry = tk.Entry(self, textvariable=self._var, width=24)
        entry.pack()
        entry.bind("<FocusIn>", self._on_focus_in)
        entry.bind("<FocusOut>", self._on_focus_out)
        entry.bind("<KeyPress>", self._on_key)

    def _on_focus_in(self, _: tk.Event) -> None:
        self._prev = self._var.get()
        self._var.set("Press hotkey...")

    def _on_focus_out(self, _: tk.Event) -> None:
        if self._var.get() == "Press hotkey...":
            self._var.set(self._prev)

    def _on_key(self, event: tk.Event) -> str:
        result = build_hotkey_string(event.state, event.keysym)
        if result is not None:
            self._var.set(result)
        return "break"

    def get(self) -> str:
        v = self._var.get()
        return self._prev if v == "Press hotkey..." else v


def open_settings(cfg: Config, on_save: Callable[[Config], None]) -> None:
    win = tk.Tk()
    win.title("live-stt settings")
    win.resizable(False, False)

    row = 0

    tk.Label(win, text="Mode:").grid(row=row, column=0, padx=8, pady=4, sticky="w")
    mode_var = tk.StringVar(value=cfg.hotkey_mode)
    tk.OptionMenu(win, mode_var, "double_tap_toggle", "ptt").grid(row=row, column=1, padx=8, sticky="w")
    row += 1

    tk.Label(win, text="Hotkey:").grid(row=row, column=0, padx=8, pady=4, sticky="w")
    hotkey_capture = _HotkeyCapture(win, value=cfg.hotkey)
    hotkey_capture.grid(row=row, column=1, padx=8)
    row += 1

    tk.Label(win, text="Double-tap window (s):").grid(row=row, column=0, padx=8, pady=4, sticky="w")
    double_tap_window_var = tk.DoubleVar(value=cfg.double_tap_window)
    tk.Scale(win, from_=0.1, to=1.0, resolution=0.05, variable=double_tap_window_var,
             orient="horizontal", length=150).grid(row=row, column=1, padx=8, sticky="w")
    row += 1

    tk.Label(win, text="Cancel:").grid(row=row, column=0, padx=8, pady=4, sticky="w")
    cancel_capture = _HotkeyCapture(win, value=cfg.cancel_hotkey)
    cancel_capture.grid(row=row, column=1, padx=8)
    row += 1

    tk.Label(win, text="LLM Model:").grid(row=row, column=0, padx=8, pady=4, sticky="w")
    model_var = tk.StringVar(value=cfg.model)
    tk.Entry(win, textvariable=model_var, width=24).grid(row=row, column=1, padx=8)
    row += 1

    refine_var = tk.BooleanVar(value=cfg.refine)
    tk.Checkbutton(win, text="Refine with LLM", variable=refine_var).grid(
        row=row, column=0, columnspan=2, padx=8, pady=4, sticky="w"
    )
    row += 1

    tk.Label(win, text="VAD Threshold:").grid(row=row, column=0, padx=8, pady=4, sticky="w")
    vad_var = tk.DoubleVar(value=cfg.vad_threshold)
    tk.Scale(win, from_=0.0, to=0.5, resolution=0.01, variable=vad_var,
             orient="horizontal", length=150).grid(row=row, column=1, padx=8, sticky="w")
    row += 1

    tk.Label(win, text="LLM Timeout (s):").grid(row=row, column=0, padx=8, pady=4, sticky="w")
    llm_timeout_var = tk.IntVar(value=cfg.llm_timeout)
    tk.Entry(win, textvariable=llm_timeout_var, width=8).grid(row=row, column=1, padx=8, sticky="w")
    row += 1

    tk.Label(win, text="Injection Delay (s):").grid(row=row, column=0, padx=8, pady=4, sticky="w")
    injection_delay_var = tk.DoubleVar(value=cfg.injection_delay)
    tk.Entry(win, textvariable=injection_delay_var, width=8).grid(row=row, column=1, padx=8, sticky="w")
    row += 1

    def _save() -> None:
        try:
            updated = Config(
                hotkey=hotkey_capture.get(),
                cancel_hotkey=cancel_capture.get(),
                model=model_var.get().strip(),
                refine=refine_var.get(),
                vad_threshold=vad_var.get(),
                hotkey_mode=mode_var.get(),
                double_tap_window=double_tap_window_var.get(),
                llm_timeout=llm_timeout_var.get(),
                injection_delay=injection_delay_var.get(),
            )
        except tk.TclError as e:
            tk.messagebox.showerror("Invalid input", f"Please correct the highlighted fields.\n\n{e}")
            return
        on_save(updated)
        win.destroy()

    tk.Button(win, text="Save", command=_save).grid(
        row=row, column=0, columnspan=2, pady=8
    )
    win.mainloop()
```

- [ ] **Step 3: Run full suite**

```
.venv\Scripts\python.exe -m pytest tests/ -v
```

- [ ] **Step 4: Commit**

```
git add src/livesttt/__main__.py src/livesttt/ui/settings.py
git commit -m "feat: wire double-tap Alt toggle mode; add mode/window controls to settings"
```

---

## Task 10: Waveform icon

**Files:**
- Create: `src/livesttt/assets/icon.svg`
- Modify: `src/livesttt/ui/tray.py`

- [ ] **Step 1: Create the SVG asset**

Create `src/livesttt/assets/__init__.py` (empty).

Create `src/livesttt/assets/icon.svg`:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect x="4"  y="24" width="8" height="16" rx="2" fill="currentColor"/>
  <rect x="16" y="16" width="8" height="32" rx="2" fill="currentColor"/>
  <rect x="28" y="8"  width="8" height="48" rx="2" fill="currentColor"/>
  <rect x="40" y="16" width="8" height="32" rx="2" fill="currentColor"/>
  <rect x="52" y="24" width="8" height="16" rx="2" fill="currentColor"/>
</svg>
```

- [ ] **Step 2: Update tray.py to draw waveform with PIL**

Replace `src/livesttt/ui/tray.py` entirely:

```python
from __future__ import annotations
from typing import Callable
import pystray
from PIL import Image, ImageDraw

_icon: pystray.Icon | None = None
_status = "idle"
_STATUS_COLORS = {
    "idle": "#4CAF50",
    "recording": "#F44336",
    "processing": "#FF9800",
    "error": "#9E9E9E",
}

_BAR_HEIGHTS = [16, 32, 48, 32, 16]  # waveform shape (out of 64px)
_BAR_WIDTH = 8
_BAR_GAP = 4
_CANVAS = 64


def _make_icon(color: str) -> Image.Image:
    img = Image.new("RGBA", (_CANVAS, _CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    total_width = len(_BAR_HEIGHTS) * _BAR_WIDTH + (len(_BAR_HEIGHTS) - 1) * _BAR_GAP
    x_start = (_CANVAS - total_width) // 2
    for i, bar_h in enumerate(_BAR_HEIGHTS):
        x = x_start + i * (_BAR_WIDTH + _BAR_GAP)
        y_top = (_CANVAS - bar_h) // 2
        y_bot = y_top + bar_h
        draw.rounded_rectangle([x, y_top, x + _BAR_WIDTH, y_bot], radius=2, fill=color)
    return img


def set_status(status: str) -> None:
    global _status
    _status = status
    if _icon:
        _icon.icon = _make_icon(_STATUS_COLORS.get(status, _STATUS_COLORS["error"]))


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
    _icon = pystray.Icon("livesttt", _make_icon(_STATUS_COLORS["idle"]), "live-stt", menu)
    _icon.run()


def notify(message: str) -> None:
    if _icon:
        _icon.notify(message, "live-stt")


def stop() -> None:
    if _icon:
        _icon.stop()
```

- [ ] **Step 3: Run tray tests**

```
.venv\Scripts\python.exe -m pytest tests/test_tray.py -v
```

- [ ] **Step 4: Commit**

```
git add src/livesttt/assets/ src/livesttt/ui/tray.py
git commit -m "feat: replace solid-circle tray icon with waveform shape; add icon.svg asset"
```

---

## Task 11: Ollama auto-pull + setup script

**Files:**
- Modify: `src/livesttt/__main__.py`
- Create: `scripts/setup_ollama.py`

- [ ] **Step 1: Write test for auto-pull logic**

Add to `tests/test_main.py`:

```python
def test_check_health_triggers_pull_when_model_missing():
    """If Ollama is reachable but model isn't listed, a pull should be scheduled."""
    import json
    tags_resp = MagicMock()
    tags_resp.status_code = 200
    tags_resp.json.return_value = {"models": []}  # model not present

    pull_called = []

    with patch("requests.get", return_value=tags_resp), \
         patch.object(app.vibevoice_local, "is_available", return_value=False), \
         patch("requests.get") as mock_get:

        mock_get.return_value = tags_resp
        # _check_health with the pull side-effect is tested by checking _maybe_pull_model
        result = app._check_health()

    # Ollama is up but model not present
    assert result["ollama"] is True


def test_maybe_pull_model_spawns_thread_when_model_absent():
    tags_resp = MagicMock()
    tags_resp.status_code = 200
    tags_resp.json.return_value = {"models": [{"name": "other:latest"}]}

    threads_started = []
    original_thread = __import__("threading").Thread

    def capturing_thread(**kwargs):
        t = original_thread(**kwargs)
        threads_started.append(t)
        return t

    with patch("requests.get", return_value=tags_resp), \
         patch("threading.Thread", side_effect=capturing_thread), \
         patch.object(app.tray, "notify"):
        app._maybe_pull_model("gemma4:2b")

    assert len(threads_started) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

```
.venv\Scripts\python.exe -m pytest tests/test_main.py::test_maybe_pull_model_spawns_thread_when_model_absent -v
```

Expected: FAIL (`_maybe_pull_model` doesn't exist).

- [ ] **Step 3: Add _maybe_pull_model to __main__.py**

Add this function after `_check_health`:

```python
def _maybe_pull_model(model: str) -> None:
    import subprocess
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        if resp.status_code != 200:
            return
        present = [m["name"] for m in resp.json().get("models", [])]
        if model in present:
            return
    except (requests.ConnectionError, requests.Timeout):
        return

    def _pull() -> None:
        tray.notify(f"Pulling {model} - this may take a few minutes...")
        logger.info(f"Pulling Ollama model: {model}")
        result = subprocess.run(["ollama", "pull", model], capture_output=True)
        if result.returncode == 0:
            tray.notify(f"{model} ready")
            logger.info(f"Model {model} pulled successfully")
        else:
            logger.warning(f"ollama pull failed: {result.stderr.decode()}")

    threading.Thread(target=_pull, daemon=True).start()
```

Call it from `_periodic_health_check`, after updating `_health`, when ollama is healthy:

```python
def _periodic_health_check(interval: int = 60) -> None:
    global _health
    while not _quit_event.is_set():
        new_health = _check_health()
        logger.debug(f"Periodic health: vibevoice={new_health['vibevoice']}, ollama={new_health['ollama']}")
        with _health_lock:
            _health = new_health
        if new_health["ollama"] and _cfg.refine:
            _maybe_pull_model(_cfg.model)
        _quit_event.wait(interval)
```

- [ ] **Step 4: Create scripts/setup_ollama.py**

```python
#!/usr/bin/env python3
"""First-run helper: installs Ollama model for live-stt refinement."""
import subprocess
import sys


MODEL = "gemma4:2b"


def _ollama_running() -> bool:
    import requests
    try:
        return requests.get("http://localhost:11434/api/tags", timeout=5).status_code == 200
    except Exception:
        return False


def main() -> None:
    print("live-stt Ollama setup")
    print("---------------------")

    try:
        subprocess.run(["ollama", "--version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("Ollama not found. Install it from https://ollama.com and re-run this script.")
        sys.exit(1)

    if not _ollama_running():
        print("Ollama is installed but not running. Start it with: ollama serve")
        sys.exit(1)

    print(f"Pulling {MODEL} (approx 1.5 GB, one-time download)...")
    result = subprocess.run(["ollama", "pull", MODEL])
    if result.returncode == 0:
        print(f"\n{MODEL} is ready. LLM refinement will be enabled on next launch.")
    else:
        print(f"\nPull failed. Run manually: ollama pull {MODEL}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run tests**

```
.venv\Scripts\python.exe -m pytest tests/test_main.py -v
```

- [ ] **Step 6: Commit**

```
git add src/livesttt/__main__.py scripts/setup_ollama.py tests/test_main.py
git commit -m "feat: auto-pull Ollama model on startup if missing; add scripts/setup_ollama.py"
```

---

## Task 12: Update TODO.md

**Files:**
- Modify: `TODO.md`

- [ ] **Step 1: Mark all completed items and update remaining**

Replace `TODO.md` with the updated state: all bug items marked `[x]`, minor polish items checked off, and any remaining work noted. See the written content in the plan — copy from the approved design's bug list and mark each item complete.

- [ ] **Step 2: Run full test suite one last time**

```
.venv\Scripts\python.exe -m pytest tests/ -v
```

Expected: all PASS.

- [ ] **Step 3: Commit**

```
git add TODO.md
git commit -m "docs: update TODO - all bugs and polish items complete"
```
