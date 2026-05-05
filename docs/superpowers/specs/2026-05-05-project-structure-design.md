# Project Structure Design

**Date:** 2026-05-05
**Topic:** Repository layout and module breakdown for `live-stt`

## Context

`live-stt` is a local, offline voice-dictation app for Windows inspired by Wispr Flow. It captures microphone audio, transcribes via VibeVoice (local STT), optionally refines with Gemma 4 (Ollama), and injects text into the active window system-wide. It will be packaged as a distributable `.exe` and installable via GitHub.

## Decisions

- **Layout:** `src/` layout (`src/livestt/`) — prevents accidental import without install, keeps PyInstaller and `pip install -e .` honest.
- **UI:** System-tray icon (pystray) + small tkinter settings window. No browser-based UI.
- **Entry point:** `python -m livestt` via `src/livestt/__main__.py`; declared in `pyproject.toml` as a GUI entry point.
- **Distribution:** `pyproject.toml` for metadata/deps; PyInstaller for `.exe` bundling (spec file at repo root).

## Top-Level Structure

```
live-stt/
├── .gitignore
├── CLAUDE.md
├── README.md
├── pyproject.toml
├── livestt.spec              ← PyInstaller spec (generated later)
├── src/
│   └── livestt/
├── tests/
└── docs/
    └── superpowers/
        └── specs/
```

## Source Modules (`src/livestt/`)

```
src/livestt/
├── __init__.py               ← version string only
├── __main__.py               ← boots tray app; orchestrates all subsystems
├── config.py                 ← loads/saves user settings via JSON (hotkey, model name, refinement toggle, VAD threshold)
│
├── audio/
│   ├── __init__.py
│   ├── capture.py            ← mic stream; push-to-talk gating via threading.Event
│   └── vad.py                ← voice activity detection; silence trimming
│
├── stt/
│   ├── __init__.py
│   └── engine.py             ← VibeVoice wrapper: transcribe(audio_bytes: bytes) -> str
│
├── llm/
│   ├── __init__.py
│   ├── client.py             ← Ollama HTTP client (POST localhost:11434/api/generate)
│   └── prompts.py            ← prompt templates: clean_up, rewrite
│
├── injection/
│   ├── __init__.py
│   └── injector.py           ← inject(text: str): clipboard write + Ctrl+V; Win32 active-window detection
│
├── hotkeys/
│   ├── __init__.py
│   └── daemon.py             ← global hotkey registration: push-to-talk, toggle, cancel
│
└── ui/
    ├── __init__.py
    ├── tray.py               ← pystray icon, right-click menu, status indicator (idle / recording / processing)
    └── settings.py           ← tkinter settings window: hotkey picker, model name, refinement toggle
```

### Module Interfaces

| Module | Public surface |
|---|---|
| `audio.capture` | `start_recording(event) -> bytes` |
| `stt.engine` | `transcribe(audio: bytes) -> str` |
| `llm.client` | `refine(text: str, mode: str) -> str` |
| `injection.injector` | `inject(text: str) -> None` |
| `hotkeys.daemon` | `register(hotkey: str, callback: Callable) -> None` |

All subsystems are wired together only in `__main__.py`. No cross-module imports between subsystems.

## Tests (`tests/`)

```
tests/
├── test_audio.py        ← mocks sounddevice
├── test_stt.py          ← mocks VibeVoice engine
├── test_llm.py          ← mocks Ollama HTTP responses
└── test_injector.py     ← mocks pyperclip and pyautogui
```

Runner: `pytest tests/`

## Packaging

- `pyproject.toml`: build backend `hatchling`; entry point `livestt = "livestt.__main__:main"`; runtime deps listed under `[project.dependencies]`.
- `pip install -e .` for local dev.
- `pyinstaller livestt.spec` to produce single-file `.exe` for distribution.
