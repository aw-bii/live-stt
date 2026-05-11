# TODO

## Blockers (completed)

- [x] **VibeVoice integration** - Now supports both local (Transformers) and HTTP (vLLM) backends. Local is preferred, falls back to HTTP.
- [x] **Install ffmpeg** - Added to README prerequisites (optional - for MP3/M4A/FLAC)

## Distribution (completed)

- [x] **PyInstaller spec** - Created `livesttt.spec` at the repo root for .exe build
- [x] **GitHub Actions CI** - Created `.github/workflows/ci.yml` that runs pytest on push/PR

## UX / Polish (completed)

- [x] **"Transcript saved" tray notification** - Implemented in `__main__.py` with `messages.INFO_TRANSCRIPTION_COMPLETE`
- [x] **Hotkey picker in settings** - Enhanced with key capture, cancel hotkey, and timeout settings
- [x] **Cancel hotkey** - Implemented with Escape key by default. Press during recording to abort.

---

## Bugs - Critical

- [x] **PTT hotkey strips modifiers - intercepts plain Space globally** - Fixed in 16162ab: `register_ptt` now uses `keyboard.add_hotkey` with the full combo string and `trigger_on_release`.

- [x] **`is_available()` loads the full model instead of checking** - Fixed in 0b5124b: now checks `import transformers` only; model loading deferred to first `transcribe()` call.

- [x] **Health monitor thread is unstoppable** - Fixed in 1826f7c: module-level `_quit_event` shared between `_periodic_health_check` and `_on_quit`.

- [x] **Race condition on `_health` dict** - Fixed in 4592139: `_health_lock` protects all reads and writes; worker threads use `_health.copy()` snapshot.

- [x] **`refine_async` ThreadPoolExecutor is never shut down** - Fixed in cb08f30: `llm_client.shutdown(cancel_futures=True)` called in `_on_quit`.

- [x] **Untracked `launch.py` shadows the real entry point** - Fixed: file deleted.

## Bugs - Important

- [ ] **File transcription injects into a random active window** - `__main__.py:112` calls `injector.inject()` after the file dialog closes, pasting into whatever window regains focus. Drop the `inject()` call from `_on_transcribe_file`; clipboard copy and `.txt` save are sufficient.

- [ ] **Tk Alt modifier mask is wrong on Windows** - `ui/settings.py:23` uses `0x8` for Alt, which is the Mod1/NumLock bit on Windows Tk. The correct mask for Alt on Windows is `0x20000`. The hotkey picker will silently produce wrong strings for any Alt combo.

- [ ] **Startup blocks the main thread before tray appears** - `main()` calls `_check_health()` synchronously, which does a 5 s Ollama HTTP probe plus a potential model load, all before `tray.run()`. Move the initial health check off the main thread so the tray icon appears immediately.

- [ ] **`transformers` and `torch` are hard dependencies** - `pyproject.toml:22-23` lists them as required, forcing a multi-GB install for every user even if they only use the HTTP backend. Move to `[project.optional-dependencies] local-stt = ["transformers>=4.50", "torch>=2.0"]`.

- [ ] **No orchestration test for `_capture_and_process`** - The main pipeline function is completely untested. Add a test that mocks `capture`, `vad`, `stt_engine`, `llm_client`, `injector`, and `tray`, and asserts the happy path, cancel path, and each failure mode.

- [ ] **`Config.stt_timeout` is declared but never used** - `config.py:20` adds the field; no code reads it. The HTTP STT call hardcodes `timeout=60` in `vibevoice.py:26`. Either wire it through or remove it.

- [ ] **Three identical `except` arms in `_capture_and_process`** - `__main__.py:58-66`: all three arms log a warning and send the same notification. Collapse to a single `except Exception` block.

- [ ] **Config not validated on save** - `ui/settings.py:102-114`: Tk `.get()` calls on `IntVar`/`DoubleVar` can raise `TclError` if the field contains non-numeric text, crashing the settings dialog without feedback. Wrap in try/except or validate before constructing `Config`.

- [ ] **Cancel only aborts during recording, not during STT/LLM** - `__main__.py:45` checks `_cancel_event` only after `start_recording` returns. Pressing Escape while transcription or refinement is running has no effect. Document this limitation or thread the cancel check through the processing stages.

## Polish - Minor

- [ ] **`INFO_TRANSCRIPTION_COMPLETE` should include the saved filename** - `messages.py` has a static string `"Transcription complete"`. The original plan specified `f"Done - transcript saved to {out_path.name}"`. Pass the path at the call site.

- [ ] **`__import__("pyperclip")` used twice as a fallback** - `__main__.py:73,115`: hoist to a normal top-level import.

- [ ] **PyInstaller spec hardcodes `.venv` path for sounddevice data** - `livesttt.spec:11`: breaks for any venv not named `.venv`. Use `collect_data_files("sounddevice")` from `PyInstaller.utils.hooks` instead.

- [ ] **`logging.py` runs `mkdir` at import time** - `logging.py:16`: importing the module from a read-only context (e.g. a test with a monkeypatched home dir) can fail. Lazy-init the log directory on first use.

- [ ] **Add `mypy` or `pyright` to CI** - The codebase uses PEP 604 union syntax and `from __future__ import annotations`; a type check step is cheap and would catch future type regressions.
