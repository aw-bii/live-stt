# Live STT

A local, offline voice-dictation app for Windows. Hold or double-tap a hotkey to record speech; it transcribes and injects the result into whatever window you have focused - no cloud, no server, no data leaves your machine.

## Features

- **Double-tap toggle or push-to-talk**: double-tap Alt to start/stop, or hold any key for push-to-talk
- **Local STT**: VibeVoice-ASR via HuggingFace Transformers (no external server needed)
- **HTTP STT fallback**: falls back to vLLM HTTP if local model is unavailable
- **Optional LLM refinement**: cleans up transcriptions with a local LLM via Ollama
- **System-wide injection**: works in any app via clipboard + Ctrl+V simulation
- **File transcription**: transcribe WAV, MP3, M4A, FLAC files from the tray menu
- **Settings UI**: configure mode, hotkey, model, VAD sensitivity, and timeouts
- **Privacy-first**: no audio or text ever leaves your computer

## Quick Start

```bash
git clone https://github.com/aw-bii/live-stt.git
cd live-stt

python -m venv .venv
.venv\Scripts\activate
pip install -e .

# Optional: set up Ollama for LLM refinement
python scripts/setup_ollama.py

python -m livesttt
```

## Usage

1. **Start the app** - it runs silently in the system tray
2. **Record** - double-tap Alt (default) to start recording; double-tap again to stop and transcribe
3. **Push-to-talk mode** - switch to PTT in Settings if you prefer hold-to-record
4. **Cancel** - press Escape during recording to abort
5. **File transcription** - right-click the tray icon, choose "Transcribe file..."
6. **Settings** - right-click the tray icon, choose "Settings" to configure:
   - Hotkey mode (double-tap toggle or push-to-talk)
   - Hotkey key
   - LLM model and refinement toggle
   - VAD threshold, timeouts, injection delay

## Prerequisites

- Windows 10+ (64-bit)
- Python 3.10+
- 8 GB RAM recommended (4 GB minimum without LLM)
- Microphone
- **ffmpeg** (optional - required for MP3, M4A, FLAC file support)
  - Install: `winget install ffmpeg`

## LLM Refinement (optional)

Install [Ollama](https://ollama.com), then run the setup helper:

```bash
python scripts/setup_ollama.py
```

This checks that Ollama is running and pulls `gemma4:2b` (~1.5 GB, one-time download). Once done, refinement is enabled automatically on next launch.

## Building the .exe

```bash
pip install pyinstaller
python scripts/make_ico.py   # generates the app icon
pyinstaller livesttt.spec
# output: dist/livesttt.exe
```

Pre-built binaries are attached to each [GitHub release](https://github.com/aw-bii/live-stt/releases).

## Running Tests

```bash
.venv\Scripts\python.exe -m pytest tests/ -v
```

## License

[MIT](LICENSE)
