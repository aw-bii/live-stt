# TODO Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement all five remaining TODO items: transcript-saved notification, cancel hotkey, hotkey-picker widget in settings, PyInstaller distribution spec, and GitHub Actions CI.

**Architecture:** Tasks 1-3 are UX features touching `ui/tray.py`, `ui/settings.py`, `config.py`, and `__main__.py`. Tasks 4-5 add build and CI config files with no runtime code changes. All five tasks are fully independent and can be done in any order.

**Tech Stack:** Python 3.10+, tkinter, pystray, keyboard library, PyInstaller, GitHub Actions

**Prerequisites (not code tasks - do these before running the app):**
- Install VibeVoice vLLM server: https://github.com/microsoft/VibeVoice/blob/main/docs/vibevoice-vllm-asr.md
- Install ffmpeg: `winget install ffmpeg` then restart terminal

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `src/livesttt/ui/tray.py` | Modify | Add `notify(message)` function |
| `src/livesttt/__main__.py` | Modify | Call `notify()` after file transcription; add `_cancel_event`, `_on_cancel`, register cancel hotkey |
| `src/livesttt/config.py` | Modify | Add `cancel_hotkey: str = "escape"` field |
| `src/livesttt/ui/settings.py` | Modify | Add `build_hotkey_string()` pure function and `_HotkeyCapture` widget; wire into `open_settings` |
| `tests/test_tray.py` | Create | Tests for `notify()` |
| `tests/test_cancel.py` | Create | Tests for cancel hotkey events |
| `tests/test_settings.py` | Create | Tests for `build_hotkey_string()` |
| `tests/test_config.py` | Modify | Add test for `cancel_hotkey` default |
| `livesttt.spec` | Create | PyInstaller single-file `.exe` spec |
| `.github/workflows/ci.yml` | Create | GitHub Actions CI - runs pytest on push |

---

## Task 1: Transcript saved tray notification

After file transcription completes, show a Windows tray notification with the output path before returning to idle. Requires adding `notify()` to `tray.py` and updating `_on_transcribe_file()` in `__main__.py`.

**Files:**
- Create: `tests/test_tray.py`
- Modify: `src/livesttt/ui/tray.py`
- Modify: `src/livesttt/__main__.py:43-58`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_tray.py`:

```python
from unittest.mock import MagicMock
import livesttt.ui.tray as tray_module


def test_notify_calls_icon_notify(monkeypatch):
    mock_icon = MagicMock()
    monkeypatch.setattr(tray_module, "_icon", mock_icon)
    tray_module.notify("Done - saved to foo.txt")
    mock_icon.notify.assert_called_once_with("Done - saved to foo.txt", "live-stt")


def test_notify_is_no_op_when_no_icon(monkeypatch):
    monkeypatch.setattr(tray_module, "_icon", None)
    tray_module.notify("any message")  # must not raise
```

- [ ] **Step 2: Run tests to verify they fail**

```
.venv\Scripts\python.exe -m pytest tests/test_tray.py -v
```

Expected: `FAILED` with `AttributeError: module 'livesttt.ui.tray' has no attribute 'notify'`

- [ ] **Step 3: Add `notify()` to `tray.py`**

In `src/livesttt/ui/tray.py`, add after `set_status`:

```python
def notify(message: str) -> None:
    if _icon:
        _icon.notify(message, "live-stt")
```

- [ ] **Step 4: Run tests to verify they pass**

```
.venv\Scripts\python.exe -m pytest tests/test_tray.py -v
```

Expected: `2 passed`

- [ ] **Step 5: Update `_on_transcribe_file` in `__main__.py`**

Replace lines 43-58 in `src/livesttt/__main__.py`. The full updated function:

```python
def _on_transcribe_file() -> None:
    path_str = tkinter.filedialog.askopenfilename(
        title="Select audio file",
        filetypes=[("Audio files", "*.wav *.mp3 *.m4a *.flac"), ("All files", "*.*")],
    )
    if not path_str:
        return
    path = Path(path_str)
    tray.set_status("processing")
    audio = reader.read_file(path)
    text = stt_engine.transcribe(audio)
    if _cfg.refine:
        text = llm_client.refine(text, "clean_up", _cfg.model)
    injector.inject(text)
    out_path = exporter.save_transcript(text, path)
    tray.notify(f"Done - transcript saved to {out_path.name}")
    tray.set_status("idle")
```

- [ ] **Step 6: Run full test suite to check for regressions**

```
.venv\Scripts\python.exe -m pytest tests/ -v
```

Expected: all existing tests pass, `test_tray.py` passes.

- [ ] **Step 7: Commit**

```bash
git add tests/test_tray.py src/livesttt/ui/tray.py src/livesttt/__main__.py
git commit -m "feat: show tray notification after file transcription completes"
```

---

## Task 2: Cancel hotkey

Wire up a hotkey (default: `escape`) to abort a recording in progress. Adds `cancel_hotkey` to `Config`, a `_cancel_event` threading flag to `__main__.py`, and registers the hotkey via `hotkey_daemon.register()`.

**Files:**
- Modify: `src/livesttt/config.py`
- Modify: `src/livesttt/__main__.py`
- Modify: `tests/test_config.py`
- Create: `tests/test_cancel.py`

- [ ] **Step 1: Write the failing config test**

Append to `tests/test_config.py`:

```python
def test_default_cancel_hotkey():
    cfg = config.Config()
    assert cfg.cancel_hotkey == "escape"


def test_cancel_hotkey_round_trips(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "config.json")
    cfg = config.Config(cancel_hotkey="ctrl+z")
    config.save(cfg)
    loaded = config.load()
    assert loaded.cancel_hotkey == "ctrl+z"
```

- [ ] **Step 2: Run tests to verify they fail**

```
.venv\Scripts\python.exe -m pytest tests/test_config.py -v
```

Expected: `FAILED` with `TypeError` on `Config()` or assertion error on missing field.

- [ ] **Step 3: Add `cancel_hotkey` to `Config`**

Replace the `Config` dataclass in `src/livesttt/config.py`:

```python
@dataclass
class Config:
    hotkey: str = "ctrl+shift+space"
    cancel_hotkey: str = "escape"
    model: str = "gemma4"
    refine: bool = True
    vad_threshold: float = 0.02
```

- [ ] **Step 4: Run config tests to verify they pass**

```
.venv\Scripts\python.exe -m pytest tests/test_config.py -v
```

Expected: all config tests pass including the two new ones.

- [ ] **Step 5: Write the failing cancel hotkey tests**

Create `tests/test_cancel.py`:

```python
import livesttt.__main__ as app


def test_on_cancel_sets_cancel_event():
    app._cancel_event.clear()
    app._on_cancel()
    assert app._cancel_event.is_set()


def test_on_cancel_sets_stop_event():
    app._stop_event.clear()
    app._on_cancel()
    assert app._stop_event.is_set()
```

- [ ] **Step 6: Run tests to verify they fail**

```
.venv\Scripts\python.exe -m pytest tests/test_cancel.py -v
```

Expected: `FAILED` with `AttributeError: module 'livesttt.__main__' has no attribute '_cancel_event'`

- [ ] **Step 7: Update `__main__.py` with cancel hotkey support**

Replace the full content of `src/livesttt/__main__.py`:

```python
from __future__ import annotations
import threading
import tkinter.filedialog
from pathlib import Path

from livesttt import config as cfg_module
from livesttt.audio import capture, vad, reader
from livesttt.stt import engine as stt_engine, vibevoice
from livesttt.llm import client as llm_client
from livesttt.injection import injector, exporter
from livesttt.hotkeys import daemon as hotkey_daemon
from livesttt.ui import tray, settings

_cfg = cfg_module.Config()
_stop_event = threading.Event()
_cancel_event = threading.Event()


def _on_ptt_press() -> None:
    _cancel_event.clear()
    _stop_event.clear()
    tray.set_status("recording")
    thread = threading.Thread(target=_capture_and_process, daemon=True)
    thread.start()


def _on_ptt_release() -> None:
    _stop_event.set()


def _on_cancel() -> None:
    _cancel_event.set()
    _stop_event.set()


def _capture_and_process() -> None:
    audio = capture.start_recording(_stop_event)
    if _cancel_event.is_set():
        tray.set_status("idle")
        return
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
    path = Path(path_str)
    tray.set_status("processing")
    audio = reader.read_file(path)
    text = stt_engine.transcribe(audio)
    if _cfg.refine:
        text = llm_client.refine(text, "clean_up", _cfg.model)
    injector.inject(text)
    out_path = exporter.save_transcript(text, path)
    tray.notify(f"Done - transcript saved to {out_path.name}")
    tray.set_status("idle")


def _on_open_settings() -> None:
    def _save(updated_cfg: cfg_module.Config) -> None:
        global _cfg
        _cfg = updated_cfg
        cfg_module.save(updated_cfg)

    settings.open_settings(_cfg, on_save=_save)


def _on_quit() -> None:
    hotkey_daemon.stop()
    tray.stop()


def main() -> None:
    global _cfg
    _cfg = cfg_module.load()
    stt_engine.set_backend(vibevoice.transcribe)

    hotkey_daemon.register_ptt(
        _cfg.hotkey.split("+")[-1],
        on_press=_on_ptt_press,
        on_release=_on_ptt_release,
    )
    hotkey_daemon.register(_cfg.cancel_hotkey, _on_cancel)

    tray.run(
        cfg=_cfg,
        on_transcribe_file=_on_transcribe_file,
        on_open_settings=_on_open_settings,
        on_quit=_on_quit,
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 8: Run full test suite**

```
.venv\Scripts\python.exe -m pytest tests/ -v
```

Expected: all tests pass including `test_cancel.py` and `test_config.py` new tests.

- [ ] **Step 9: Commit**

```bash
git add src/livesttt/config.py src/livesttt/__main__.py tests/test_config.py tests/test_cancel.py
git commit -m "feat: add cancel hotkey to abort recording in progress"
```

---

## Task 3: Hotkey picker in settings

Replace the plain text `Entry` for the hotkey field in the settings window with a key-capture widget: click the field, press the desired combo, it fills in automatically.

The key logic is extracted into a pure function `build_hotkey_string(state, keysym)` so it can be unit tested without tkinter. The `_HotkeyCapture` widget wraps it in a `tk.Frame`.

**tkinter state bit flags (Windows):**
- `0x4` = Control held
- `0x1` = Shift held
- `0x8` = Alt held

**Files:**
- Modify: `src/livesttt/ui/settings.py`
- Create: `tests/test_settings.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_settings.py`:

```python
from livesttt.ui.settings import build_hotkey_string


def test_returns_none_for_control_l():
    assert build_hotkey_string(0, "Control_L") is None


def test_returns_none_for_shift_r():
    assert build_hotkey_string(0, "Shift_R") is None


def test_returns_none_for_alt_l():
    assert build_hotkey_string(0, "Alt_L") is None


def test_plain_key_no_modifiers():
    assert build_hotkey_string(0, "space") == "space"


def test_ctrl_modifier():
    assert build_hotkey_string(0x4, "space") == "ctrl+space"


def test_ctrl_shift_modifier():
    assert build_hotkey_string(0x4 | 0x1, "space") == "ctrl+shift+space"


def test_alt_modifier():
    assert build_hotkey_string(0x8, "f9") == "alt+f9"


def test_keysym_is_lowercased():
    assert build_hotkey_string(0, "Return") == "return"


def test_ctrl_shift_key_matches_config_default():
    assert build_hotkey_string(0x4 | 0x1, "space") == "ctrl+shift+space"
```

- [ ] **Step 2: Run tests to verify they fail**

```
.venv\Scripts\python.exe -m pytest tests/test_settings.py -v
```

Expected: `FAILED` with `ImportError: cannot import name 'build_hotkey_string'`

- [ ] **Step 3: Replace `settings.py` with hotkey-capture widget**

Replace the full content of `src/livesttt/ui/settings.py`:

```python
from __future__ import annotations
import tkinter as tk
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
    if state & 0x8:
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
        return self._var.get()


def open_settings(cfg: Config, on_save: Callable[[Config], None]) -> None:
    win = tk.Tk()
    win.title("live-stt settings")
    win.resizable(False, False)

    tk.Label(win, text="Hotkey:").grid(row=0, column=0, padx=8, pady=4, sticky="w")
    hotkey_capture = _HotkeyCapture(win, value=cfg.hotkey)
    hotkey_capture.grid(row=0, column=1, padx=8)

    tk.Label(win, text="Model:").grid(row=1, column=0, padx=8, pady=4, sticky="w")
    model_var = tk.StringVar(value=cfg.model)
    tk.Entry(win, textvariable=model_var, width=24).grid(row=1, column=1, padx=8)

    refine_var = tk.BooleanVar(value=cfg.refine)
    tk.Checkbutton(win, text="Refine with LLM", variable=refine_var).grid(
        row=2, column=0, columnspan=2, padx=8, pady=4, sticky="w"
    )

    def _save() -> None:
        updated = Config(
            hotkey=hotkey_capture.get(),
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

- [ ] **Step 4: Run tests to verify they pass**

```
.venv\Scripts\python.exe -m pytest tests/test_settings.py -v
```

Expected: `9 passed`

- [ ] **Step 5: Run full test suite**

```
.venv\Scripts\python.exe -m pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/livesttt/ui/settings.py tests/test_settings.py
git commit -m "feat: replace hotkey text field with key-capture widget in settings"
```

---

## Task 4: PyInstaller distribution spec

Create a `livesttt.spec` at the repo root to produce a single-file `dist/livesttt.exe` for Windows distribution. The spec sets `console=False` (no terminal window), includes hidden imports needed for pystray's Win32 backend, and uses `src/livesttt/__main__.py` as the entry point.

**Files:**
- Create: `livesttt.spec`

- [ ] **Step 1: Install PyInstaller into the venv**

```
.venv\Scripts\pip.exe install pyinstaller
```

Expected: `Successfully installed pyinstaller-...`

- [ ] **Step 2: Create `livesttt.spec`**

Create `livesttt.spec` at the repo root:

```python
block_cipher = None

a = Analysis(
    ['src/livesttt/__main__.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'pystray._win32',
        'PIL._tkinter_finder',
        'win32api',
        'win32con',
        'win32gui',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zlib, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='livesttt',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
```

- [ ] **Step 3: Build the executable**

```
.venv\Scripts\pyinstaller.exe livesttt.spec --noconfirm
```

Expected: build completes, `dist/livesttt.exe` is created.

- [ ] **Step 4: Verify the executable exists**

```
dir dist\livesttt.exe
```

Expected: file exists and is a non-zero size `.exe`.

- [ ] **Step 5: Add build artifacts to `.gitignore`**

Append to `.gitignore` (create it if missing):

```
build/
dist/
*.spec.bak
```

Note: commit `livesttt.spec` but not `build/` or `dist/`.

- [ ] **Step 6: Commit**

```bash
git add livesttt.spec .gitignore
git commit -m "build: add PyInstaller spec for single-file Windows exe"
```

---

## Task 5: GitHub Actions CI

Add a CI workflow that installs dependencies and runs pytest on every push and pull request to `master`. Uses `windows-latest` because `pywin32` is a hard dependency that won't install on Linux.

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create the workflow directory**

```bash
mkdir -p .github/workflows
```

- [ ] **Step 2: Create `.github/workflows/ci.yml`**

```yaml
name: CI

on:
  push:
    branches: [master]
  pull_request:
    branches: [master]

jobs:
  test:
    runs-on: windows-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Run tests
        run: python -m pytest tests/ -v
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add GitHub Actions workflow to run pytest on push"
```

---

## Self-Review

**Spec coverage check:**
- Transcript saved notification: Task 1 - covered
- Install ffmpeg / VibeVoice: noted as prerequisites, not code tasks - correct
- PyInstaller spec: Task 4 - covered
- GitHub Actions CI: Task 5 - covered
- Hotkey picker in settings: Task 3 - covered
- Cancel hotkey: Task 2 - covered

**Placeholder scan:** No TBD, TODO, "similar to Task N", or "add appropriate error handling" placeholders found. Every code step shows the complete implementation.

**Type consistency:**
- `build_hotkey_string(state: int, keysym: str) -> str | None` defined in Task 3 Step 3, used in tests in Task 3 Step 1 - consistent.
- `notify(message: str) -> None` defined in Task 1 Step 3, called in Task 1 Step 5 as `tray.notify(...)` - consistent.
- `_cancel_event` and `_on_cancel` defined in Task 2 Step 7, tested in Task 2 Step 5 via module import - consistent.
- `cancel_hotkey: str` added to `Config` in Task 2 Step 3, accessed as `_cfg.cancel_hotkey` in Task 2 Step 7 - consistent.
- `_HotkeyCapture.get()` defined in Task 3 Step 3, called as `hotkey_capture.get()` in `_save()` in the same step - consistent.
