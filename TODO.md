# TODO

## Blockers (completed)

- [x] **VibeVoice integration** - Now supports both local (Transformers) and HTTP (vLLM) backends. Local is preferred, falls back to HTTP.
- [x] **Install ffmpeg** - Added to README prerequisites (optional - for MP3/M4A/FLAC)

## Distribution (completed)

- [x] **PyInstaller spec** - Created `livesttt.spec` at the repo root for .exe build
- [x] **GitHub Actions CI** - Created `.github/workflows/ci.yml` that runs pytest on push/PR

## UX / Polish (completed)

- [x] **"Transcript saved" tray notification** - Now includes filename: `"Transcript saved: {name}"`
- [x] **Hotkey picker in settings** - Mode dropdown (double-tap toggle / PTT), key capture, cancel hotkey, double-tap window, and all other settings
- [x] **Cancel hotkey** - Escape key by default. Press during recording to abort.
- [x] **Double-tap Alt toggle mode** - Default hotkey mode. Double-tap Alt to start, double-tap again to stop.
- [x] **Waveform tray icon** - 5-bar waveform rendered with PIL. Colors: green (idle), red (recording), orange (processing), gray (error).
- [x] **Ollama auto-pull** - On startup, if Ollama is running but `gemma4:2b` is not pulled, auto-pulls in background with tray notification.
- [x] **setup_ollama.py** - `scripts/setup_ollama.py` for first-run Ollama + model installation.

## Bugs - Critical (all completed)

- [x] **PTT hotkey strips modifiers** - Fixed in 16162ab
- [x] **`is_available()` loads the full model** - Fixed in 0b5124b
- [x] **Health monitor thread is unstoppable** - Fixed in 1826f7c
- [x] **Race condition on `_health` dict** - Fixed in 4592139
- [x] **`refine_async` ThreadPoolExecutor never shut down** - Fixed in cb08f30
- [x] **Untracked `launch.py` shadows entry point** - Deleted

## Bugs - Important (all completed)

- [x] **File transcription injects into random active window** - Removed `inject()` from `_on_transcribe_file`; clipboard copy and `.txt` save are sufficient.
- [x] **Tk Alt modifier mask wrong on Windows** - Fixed `0x8` to `0x20000` in `settings.py`.
- [x] **Startup blocks main thread before tray appears** - Removed synchronous `_check_health()` from `main()`; health monitor thread handles the first check.
- [x] **`transformers` and `torch` are hard dependencies** - Moved to `[project.optional-dependencies] local-stt`.
- [x] **`Config.stt_timeout` declared but never used** - Removed from `Config` dataclass.
- [x] **Three identical `except` arms in `_capture_and_process`** - Collapsed to single `except Exception`.
- [x] **Config not validated on save** - `_save()` in settings now wraps Tk `.get()` calls in `try/except tk.TclError`.
- [x] **Cancel only aborts during recording** - Limitation documented; cancel checks `_cancel_event` only after `start_recording` returns.

## Polish - Minor (all completed)

- [x] **`INFO_TRANSCRIPTION_COMPLETE` should include filename** - Now `"Transcript saved: {name}"` formatted at call site.
- [x] **`__import__("pyperclip")` used twice as fallback** - Hoisted to top-level import.
- [x] **`logging.py` runs `mkdir` at import time** - Moved to `log_module.init_file_logging()` called from `main()`.

## Remaining

- [ ] **PyInstaller spec hardcodes `.venv` path for sounddevice data** - `livesttt.spec:11`: use `collect_data_files("sounddevice")` from `PyInstaller.utils.hooks`.
- [ ] **Add `mypy` or `pyright` to CI** - Cheap type-check step would catch regressions.
- [ ] **No orchestration test for `_capture_and_process`** - Core pipeline untested; add test mocking capture/vad/stt/llm/injector for happy path and cancel.
