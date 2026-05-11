# Critical Bugs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix six critical bugs in one branch so the app starts cleanly, runs safely under concurrent access, and shuts down completely.

**Architecture:** All changes are minimal and surgical - no new modules, no new public APIs. Four fixes touch `__main__.py`, one touches `stt/vibevoice_local.py`, one touches `llm/client.py`, and `launch.py` is deleted.

**Tech Stack:** Python, `threading`, `keyboard` library, `concurrent.futures.ThreadPoolExecutor`

---

## File Map

| File | What changes |
| --- | --- |
| `src/livesttt/stt/vibevoice_local.py` | `is_available()` becomes an import check only |
| `src/livesttt/hotkeys/daemon.py` | `register_ptt` uses `add_hotkey` with full combo string |
| `src/livesttt/__main__.py` | Module-level `_quit_event` + `_health_lock`; PTT call site; `_on_quit` wires shutdown |
| `src/livesttt/llm/client.py` | Add `shutdown()` function |
| `tests/test_vibevoice_local.py` | Update `test_is_available_returns_true_when_model_loads` |
| `tests/test_hotkeys.py` | Update `test_register_ptt_hooks_press_and_release` |
| `tests/test_main_shutdown.py` | New - health monitor stop event test |
| `launch.py` | Delete |

---

## Task 1: Fix `is_available()` - decouple from model loading

**Spec:** `stt/vibevoice_local.py:42-47` currently calls `_get_model()`, which downloads multi-GB weights. Replace with a lightweight import check.

**Files:**
- Modify: `src/livesttt/stt/vibevoice_local.py:42-47`
- Modify: `tests/test_vibevoice_local.py`

- [ ] **Step 1: Update the existing test to use import-level mocking**

Replace `test_is_available_returns_true_when_model_loads` in `tests/test_vibevoice_local.py`:

```python
import pytest
from unittest.mock import patch, MagicMock

from livesttt.stt import vibevoice_local


def test_is_available_returns_false_when_import_fails():
    with patch.dict("sys.modules", {"transformers": None}):
        result = vibevoice_local.is_available()
    assert result is False


def test_is_available_returns_true_when_transformers_importable():
    with patch.dict("sys.modules", {"transformers": MagicMock()}):
        result = vibevoice_local.is_available()
    assert result is True
```

- [ ] **Step 2: Run the updated test to verify it fails (implementation not changed yet)**

```
.venv\Scripts\python.exe -m pytest tests/test_vibevoice_local.py::test_is_available_returns_true_when_transformers_importable -v
```

Expected: FAIL - the current implementation calls `_get_model()`, not an import check.

- [ ] **Step 3: Replace `is_available()` in `vibevoice_local.py`**

Replace lines 42-47 of `src/livesttt/stt/vibevoice_local.py`:

```python
def is_available() -> bool:
    try:
        import transformers  # noqa: F401
        return True
    except ImportError:
        return False
```

- [ ] **Step 4: Run all vibevoice_local tests**

```
.venv\Scripts\python.exe -m pytest tests/test_vibevoice_local.py -v
```

Expected: both tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/livesttt/stt/vibevoice_local.py tests/test_vibevoice_local.py
git commit -m "fix: decouple is_available() from model loading - check import only"
```

---

## Task 2: Fix PTT hotkey - respect full combo string

**Spec:** `__main__.py:198` strips modifiers by splitting on `"+"` and taking only the last token, then passes it to `register_ptt` with `suppress=True`. This suppresses every press of the bare key system-wide. Fix: update `register_ptt` to accept the full combo string and use `keyboard.add_hotkey` with `trigger_on_release`.

**Files:**
- Modify: `src/livesttt/hotkeys/daemon.py`
- Modify: `src/livesttt/__main__.py:197-201`
- Modify: `tests/test_hotkeys.py`

- [ ] **Step 1: Update `test_register_ptt_hooks_press_and_release` to assert full combo + `add_hotkey`**

Replace the existing test in `tests/test_hotkeys.py`:

```python
from unittest.mock import patch, MagicMock, call
from livesttt.hotkeys import daemon


def test_register_calls_keyboard_add_hotkey():
    cb = MagicMock()
    with patch("keyboard.add_hotkey") as mock_add:
        daemon.register("ctrl+shift+space", cb)
    mock_add.assert_called_once_with("ctrl+shift+space", cb)


def test_register_ptt_hooks_press_and_release_with_full_combo():
    on_press = MagicMock()
    on_release = MagicMock()
    with patch("keyboard.add_hotkey") as mock_add:
        daemon.register_ptt("ctrl+shift+space", on_press, on_release)
    assert mock_add.call_count == 2
    calls = mock_add.call_args_list
    assert calls[0][0][0] == "ctrl+shift+space"
    assert calls[0][0][1] == on_press
    assert calls[0][1]["suppress"] is True
    assert calls[0][1]["trigger_on_release"] is False
    assert calls[1][0][0] == "ctrl+shift+space"
    assert calls[1][0][1] == on_release
    assert calls[1][1]["suppress"] is True
    assert calls[1][1]["trigger_on_release"] is True


def test_stop_unhooks_all():
    with patch("keyboard.unhook_all") as mock_unhook:
        daemon.stop()
    mock_unhook.assert_called_once()
```

- [ ] **Step 2: Run the new test to verify it fails**

```
.venv\Scripts\python.exe -m pytest tests/test_hotkeys.py::test_register_ptt_hooks_press_and_release_with_full_combo -v
```

Expected: FAIL - current `register_ptt` uses `on_press_key`/`on_release_key`.

- [ ] **Step 3: Update `daemon.register_ptt` to use `add_hotkey` with full combo**

Replace the full `register_ptt` function in `src/livesttt/hotkeys/daemon.py`:

```python
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


def stop() -> None:
    keyboard.unhook_all()
```

- [ ] **Step 4: Update the call site in `__main__.py` to pass the full hotkey string**

Replace lines 197-201 in `src/livesttt/__main__.py`:

```python
    hotkey_daemon.register_ptt(
        _cfg.hotkey,
        on_press=_on_ptt_press,
        on_release=_on_ptt_release,
    )
```

- [ ] **Step 5: Run all hotkey tests**

```
.venv\Scripts\python.exe -m pytest tests/test_hotkeys.py -v
```

Expected: all three tests PASS.

- [ ] **Step 6: Commit**

```bash
git add src/livesttt/hotkeys/daemon.py src/livesttt/__main__.py tests/test_hotkeys.py
git commit -m "fix: PTT hotkey respects full combo string - no longer suppresses bare key globally"
```

---

## Task 3: Fix health monitor - module-level quit event

**Spec:** `__main__.py:173` creates a fresh `threading.Event()` each loop iteration, so `_on_quit` can never wake the sleeping thread. Replace with a shared module-level `_quit_event`.

**Files:**
- Modify: `src/livesttt/__main__.py:140-144,165-173`
- Create: `tests/test_main_shutdown.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_main_shutdown.py`:

```python
import threading
from unittest.mock import patch
from livesttt import __main__ as app


def test_health_monitor_stops_when_quit_event_is_set():
    app._quit_event.clear()

    with patch.object(app, "_check_health", return_value={"vibevoice": False, "ollama": False}):
        thread = threading.Thread(
            target=app._periodic_health_check,
            args=(0,),
            daemon=True,
        )
        thread.start()
        app._quit_event.set()
        thread.join(timeout=2.0)

    assert not thread.is_alive(), "Health monitor did not stop after _quit_event was set"
```

- [ ] **Step 2: Run the test to verify it fails**

```
.venv\Scripts\python.exe -m pytest tests/test_main_shutdown.py -v
```

Expected: FAIL - the current implementation creates a new `threading.Event()` each iteration and never exits.

- [ ] **Step 3: Add `_quit_event` at module level and update `_periodic_health_check` and `_on_quit`**

In `src/livesttt/__main__.py`, make the following changes:

**Replace the module-level `_health_monitor_running` declaration (line 165):**

```python
_quit_event = threading.Event()
```

**Replace `_periodic_health_check` (lines 168-173):**

```python
def _periodic_health_check(interval: int = 60) -> None:
    global _health
    while not _quit_event.is_set():
        _health = _check_health()
        logger.debug(f"Periodic health: vibevoice={_health['vibevoice']}, ollama={_health['ollama']}")
        _quit_event.wait(interval)
```

**Replace `_on_quit` (lines 140-144):**

```python
def _on_quit() -> None:
    _quit_event.set()
    hotkey_daemon.stop()
    tray.stop()
```

- [ ] **Step 4: Run the shutdown test**

```
.venv\Scripts\python.exe -m pytest tests/test_main_shutdown.py -v
```

Expected: PASS.

- [ ] **Step 5: Run the full test suite to check for regressions**

```
.venv\Scripts\python.exe -m pytest tests/ -v
```

Expected: all existing tests PASS.

- [ ] **Step 6: Commit**

```bash
git add src/livesttt/__main__.py tests/test_main_shutdown.py
git commit -m "fix: health monitor thread now stops cleanly via shared _quit_event"
```

---

## Task 4: Fix `_health` race condition

**Spec:** `__main__.py:54,67,171` - the monitor thread reassigns `_health` while worker threads read it. Protect with a module-level `threading.Lock`.

**Files:**
- Modify: `src/livesttt/__main__.py:22,54,67,103,109,169-173`

No new tests needed - thread safety is structural and the existing suite provides regression coverage.

- [ ] **Step 1: Add `_health_lock` at module level in `__main__.py`**

After the `_health = {...}` declaration (line 22), add:

```python
_health = {"vibevoice": False, "ollama": False}
_health_lock = threading.Lock()
```

- [ ] **Step 2: Protect the write in `_periodic_health_check`**

Replace the assignment inside `_periodic_health_check`:

```python
def _periodic_health_check(interval: int = 60) -> None:
    global _health
    while not _quit_event.is_set():
        new_health = _check_health()
        logger.debug(f"Periodic health: vibevoice={new_health['vibevoice']}, ollama={new_health['ollama']}")
        with _health_lock:
            _health = new_health
        _quit_event.wait(interval)
```

- [ ] **Step 3: Protect the reads in `_capture_and_process`**

At the top of `_capture_and_process`, take a snapshot under the lock. Replace the function's try-block opening:

```python
def _capture_and_process() -> None:
    with _health_lock:
        health = _health.copy()
    try:
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
        if _cfg.refine and health["ollama"]:
            try:
                future = llm_client.refine_async(text, "clean_up", _cfg.model, _cfg.llm_timeout)
                text = future.result(timeout=_cfg.llm_timeout + 5)
            except requests.ConnectionError as e:
                logger.warning(f"LLM refinement failed: {e}")
                tray.notify(messages.ERROR_OLLAMA_UNAVAILABLE)
            except TimeoutError as e:
                logger.warning(f"LLM refinement timed out: {e}")
                tray.notify(messages.ERROR_OLLAMA_UNAVAILABLE)
            except Exception as e:
                logger.warning(f"LLM refinement failed: {e}")
                tray.notify(messages.ERROR_OLLAMA_UNAVAILABLE)
        elif _cfg.refine and not health["ollama"]:
            logger.info("Skipping refinement - Ollama unavailable")
        try:
            injector.inject(text, _cfg.injection_delay)
        except Exception as e:
            logger.warning(f"Injection failed: {e}")
            pyperclip = __import__("pyperclip")
            pyperclip.copy(text)
            tray.notify(messages.ERROR_INJECTION_FAILED)
        tray.set_status("idle")
    except (requests.ConnectionError, requests.Timeout) as e:
        logger.error(f"VibeVoice unavailable: {e}")
        tray.set_status("error")
        tray.notify(messages.ERROR_VIBEVOICE_UNAVAILABLE)
    except Exception as e:
        logger.exception(f"Transcription failed: {e}")
        tray.set_status("error")
        tray.notify(messages.ERROR_TRANSCRIPTION_FAILED)
```

- [ ] **Step 4: Protect the reads in `_on_transcribe_file`**

At the top of the try-block in `_on_transcribe_file`, take a snapshot:

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
        try:
            injector.inject(text, _cfg.injection_delay)
        except Exception as e:
            logger.warning(f"Injection failed: {e}")
            pyperclip = __import__("pyperclip")
            pyperclip.copy(text)
            tray.notify(messages.ERROR_INJECTION_FAILED)
        out_path = exporter.save_transcript(text, path)
        tray.notify(messages.INFO_TRANSCRIPTION_COMPLETE)
        tray.set_status("idle")
    except (requests.ConnectionError, requests.Timeout) as e:
        logger.error(f"VibeVoice unavailable: {e}")
        tray.set_status("error")
        tray.notify(messages.ERROR_VIBEVOICE_UNAVAILABLE)
    except Exception as e:
        logger.exception(f"File transcription failed: {e}")
        tray.set_status("error")
        tray.notify(messages.ERROR_TRANSCRIPTION_FAILED)
```

- [ ] **Step 5: Run the full test suite**

```
.venv\Scripts\python.exe -m pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add src/livesttt/__main__.py
git commit -m "fix: protect _health dict with threading.Lock to eliminate race condition"
```

---

## Task 5: Fix executor shutdown

**Spec:** `llm/client.py:7` - the `ThreadPoolExecutor` is never shut down on quit, which can hang the process on Windows. Expose a `shutdown()` function and call it from `_on_quit`.

**Files:**
- Modify: `src/livesttt/llm/client.py`
- Modify: `src/livesttt/__main__.py:140-144`

- [ ] **Step 1: Add `shutdown()` to `llm/client.py`**

Append to `src/livesttt/llm/client.py`:

```python
import requests
from concurrent.futures import ThreadPoolExecutor, Future
from livesttt.llm.prompts import get_prompt

OLLAMA_URL = "http://localhost:11434/api/generate"

_executor = ThreadPoolExecutor(max_workers=1)


def refine(text: str, mode: str, model: str, timeout: int = 30) -> str:
    payload = {
        "model": model,
        "prompt": get_prompt(mode, text),
        "stream": False,
    }
    resp = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()["response"].strip()


def refine_async(text: str, mode: str, model: str, timeout: int = 30) -> Future:
    return _executor.submit(refine, text, mode, model, timeout)


def shutdown() -> None:
    _executor.shutdown(cancel_futures=True)
```

- [ ] **Step 2: Call `llm_client.shutdown()` in `_on_quit`**

Replace `_on_quit` in `src/livesttt/__main__.py`:

```python
def _on_quit() -> None:
    _quit_event.set()
    llm_client.shutdown()
    hotkey_daemon.stop()
    tray.stop()
```

- [ ] **Step 3: Run the full test suite**

```
.venv\Scripts\python.exe -m pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 4: Commit**

```bash
git add src/livesttt/llm/client.py src/livesttt/__main__.py
git commit -m "fix: shut down LLM executor on quit to prevent Windows process hang"
```

---

## Task 6: Delete stray `launch.py`

**Spec:** An untracked `launch.py` at the repo root has broken behavior and shadows the real entry point. Delete it.

**Files:**
- Delete: `launch.py`

- [ ] **Step 1: Confirm it is untracked**

```bash
git status launch.py
```

Expected output contains: `?? launch.py`

- [ ] **Step 2: Delete the file**

```bash
rm launch.py
```

- [ ] **Step 3: Verify it is gone**

```bash
git status
```

Expected: `launch.py` no longer appears in the output.

- [ ] **Step 4: Run the full test suite one final time**

```
.venv\Scripts\python.exe -m pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git commit --allow-empty -m "fix: delete stray launch.py that shadowed the real entry point"
```

Note: since `launch.py` was untracked, git has nothing to stage. The commit is a marker that the cleanup was intentional. If you prefer, skip the commit - the previous commits tell the full story.
