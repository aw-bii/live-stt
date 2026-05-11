<p align="center">
  <img src="src/bertytype/assets/icon.png" alt="BertyType" width="128" height="128" />
</p>

<h1 align="center">BertyType</h1>

<p align="center">
  <strong>Local, offline voice dictation for Windows</strong><br>
  100% on-device speech-to-text · Zero cloud costs · Privacy by default
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License" /></a>
  <img src="https://img.shields.io/badge/platform-Windows%2010%2B-lightgrey?logo=windows" alt="Windows 10+" />
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white" alt="Python 3.10+" />
  <a href="https://github.com/aw-bii/bertytype/actions"><img src="https://github.com/aw-bii/bertytype/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
</p>

---

## What is BertyType?

BertyType is a **lightweight Windows tray app** that captures microphone audio, transcribes speech using VibeVoice, optionally refines the text with a local LLM, and injects the result into whatever window you have focused - system-wide, without any cloud dependency.

### Dictation

Double-tap Alt (or hold for push-to-talk) to record. On release, transcribed text is pasted at your cursor via clipboard injection. Works in any application: browsers, IDEs, chat apps, Office, and more.

### LLM Refinement (optional)

When Ollama is running locally, transcriptions are passed through Gemma 4 2B for clean-up: filler word removal, punctuation correction, and natural formatting. Toggle it on or off at any time from Settings.

---

## Features

- **Double-tap toggle and push-to-talk** - double-tap Alt to start/stop recording hands-free, or hold any hotkey for quick PTT mode. Configurable from Settings.
- **Local STT via VibeVoice** - uses `microsoft/VibeVoice-ASR-HF` via HuggingFace Transformers. Falls back to an HTTP vLLM backend if the local model is unavailable.
- **Optional LLM refinement** - cleans up transcriptions with Gemma 4 2B via Ollama. Auto-pulls the model in the background if Ollama is running but the model is missing.
- **System-wide injection** - injects text into any focused window via clipboard + Ctrl+V simulation. Falls back to clipboard copy with a tray notification if injection fails.
- **File transcription** - right-click the tray icon to transcribe WAV, MP3, M4A, or FLAC files. Transcript saved as `.txt` alongside the source file and copied to clipboard.
- **Voice activity detection** - silence trimming via energy-based VAD before transcription. Threshold is configurable from Settings.
- **Waveform tray icon** - five-bar waveform rendered with PIL. Color-coded by state: green (idle), red (recording), orange (processing), grey (error).
- **Settings UI** - configure hotkey mode, hotkey key, double-tap window, cancel hotkey, LLM model, VAD threshold, refinement toggle, and injection delay.
- **Health monitoring** - background thread polls VibeVoice and Ollama availability every 60 seconds and updates the pipeline accordingly.
- **Cancel at any time** - press Escape during recording to abort without transcribing.

---

## Install

### Download (recommended)

Download the latest `bertytype.exe` from [Releases](https://github.com/aw-bii/bertytype/releases), place it anywhere, and run it. No installer needed - the app appears in the system tray.

> **First run:** the VibeVoice speech model (~1 GB) downloads automatically on your first transcription. Expect a 1-2 minute delay the first time.
> **Hotkeys:** run as Administrator if global hotkeys do not register. The `keyboard` library requires elevated permissions on some Windows configurations.

To start on login, place a shortcut to the exe in `shell:startup` (Win+R to open it).

### From source

**Requirements:** Windows 10+, Python 3.10+

```bash
git clone https://github.com/aw-bii/bertytype.git
cd bertytype

python -m venv .venv
.venv\Scripts\activate
pip install -e .

python -m bertytype
```

### LLM refinement setup (optional)

Install [Ollama](https://ollama.com), then run the setup helper:

```bash
python scripts/setup_ollama.py
```

This verifies Ollama is running and pulls `gemma4:2b` (~1.5 GB, one-time download). Once done, refinement enables automatically on next launch.

### Build the exe

```bash
pip install pyinstaller
python scripts/make_ico.py
pyinstaller bertytype.spec
# output: dist/bertytype.exe
```

---

## Models

| Model | Backend | Size | Notes |
| --- | --- | --- | --- |
| **VibeVoice ASR** (default) | HuggingFace Transformers (local) | ~1 GB | `microsoft/VibeVoice-ASR-HF`; downloaded on first use |
| VibeVoice ASR | vLLM HTTP | - | Fallback if local model unavailable; requires a running vLLM server at `localhost:8000` |
| **Gemma 4 2B** (refinement) | Ollama | ~1.5 GB | Optional; `gemma4:2b`; auto-pulled if Ollama is running |

---

## Permissions

| Permission | Why |
| --- | --- |
| **Microphone** | Record audio for dictation and file transcription |
| **Clipboard access** | Write transcribed text for injection via Ctrl+V |
| **Global input monitoring** | Detect hotkey presses system-wide via the `keyboard` library |
| **Administrator** *(may be required)* | `keyboard` requires elevated permissions on some Windows configurations |

---

## Architecture

```text
+------------------------------------------------------------------+
|  Python Tray App                                                 |
|  +------------------+   audio   +--------------+                |
|  |  Hotkey Daemon   | --------> |  Audio Loop  |                |
|  |  (keyboard lib)  |           |  + VAD trim  |                |
|  +------------------+           +--------------+                |
|                                        |                         |
|                                   raw audio                      |
|                                        v                         |
|                               +-----------------+               |
|                               |  STT Engine     |               |
|                               |  VibeVoice ASR  |               |
|                               |  (local / HTTP) |               |
|                               +-----------------+               |
|                                        |                         |
|                                   raw text                       |
|                                        v                         |
|                               +-----------------+               |
|                               |  LLM Refinement |               |
|                               |  Gemma 4 via    |               |
|                               |  Ollama (opt.)  |               |
|                               +-----------------+               |
|                                        |                         |
|                                  refined text                    |
|                                        v                         |
|                               +-----------------+               |
|                               |  Text Injector  |               |
|                               |  clipboard +    |               |
|                               |  Ctrl+V sim.    |               |
|                               +-----------------+               |
|                                                                  |
|  pystray + Pillow tray icon  |  tkinter Settings UI             |
+------------------------------------------------------------------+
```

---

## Tech Stack

| Component | Technology |
| --- | --- |
| App | Python 3.10+, pystray, Pillow |
| STT | [VibeVoice-ASR-HF](https://huggingface.co/microsoft/VibeVoice-ASR-HF) via HuggingFace Transformers |
| LLM refinement | [Gemma 4 2B](https://ollama.com/library/gemma4) via [Ollama](https://ollama.com) HTTP API |
| Audio capture | sounddevice + pydub |
| Voice activity detection | Energy-based VAD (scipy) |
| Text injection | pyperclip + pyautogui (clipboard + Ctrl+V simulation) |
| Hotkeys | keyboard (global hook) |
| Settings UI | tkinter |
| Tray icon | pystray + PIL `ImageDraw` (waveform rendered at runtime) |
| Packaging | PyInstaller (single-file exe) |
| Logging | loguru |
| CI | GitHub Actions (pytest + mypy on push/PR) |

---

## Contributing

Contributions welcome. To get started:

```bash
git clone https://github.com/aw-bii/bertytype.git
cd bertytype
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
python -m pytest tests/ -v
```

82 tests covering the core transcription pipeline, hotkey daemon (PTT and double-tap toggle), settings UI, config validation, VAD, audio capture, text injection, LLM client, health monitoring, and file transcription.

Please open an issue before submitting large PRs.

---

## Acknowledgements

- [VibeVoice-ASR-HF](https://huggingface.co/microsoft/VibeVoice-ASR-HF) by Microsoft - local speech recognition model
- [Ollama](https://ollama.com) - local LLM inference runtime
- [Gemma 4](https://ollama.com/library/gemma4) by Google - LLM used for transcription refinement
- [pystray](https://github.com/moses-palmer/pystray) - system tray integration for Python
- [keyboard](https://github.com/boppreh/keyboard) - global hotkey hooks for Python on Windows

---

## License

[MIT](LICENSE) - free and open source.
