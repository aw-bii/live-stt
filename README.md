# Live STT

A local, offline voice-dictation app for Windows that provides real-time speech-to-text transcription with optional LLM refinement.

## Overview

Live STT captures microphone audio, transcribes speech using VibeVoice (local STT via Transformers), optionally refines the text with a local LLM (via Ollama), and injects the result into whatever window you have focused - all without any cloud dependency.

## Features

- **Real-time Speech Recognition**: Push-to-talk recording (hold hotkey)
- **Local STT**: Uses VibeVoice-ASR via HuggingFace Transformers (no external server needed)
- **Fallback STT**: Falls back to vLLM HTTP if local model unavailable
- **Optional LLM Refinement**: Improve transcriptions with local LLM via Ollama
- **System-wide Injection**: Works in any application via clipboard + Ctrl+V
- **File Transcription**: Transcribe existing audio files (WAV, MP3, M4A, FLAC)
- **Customizable Hotkeys**: Configure push-to-talk and cancel hotkeys
- **Settings UI**: Configure model, VAD threshold, timeouts, and more
- **Health Monitoring**: Automatic detection of service availability
- **Privacy First**: No data leaves your computer

## Documentation

For detailed information about the project:

- **[PRODUCT.md](PRODUCT.md)** - Product requirements, vision, and user stories
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and component design
- **[AGENTS.md](AGENTS.md)** - Agent configurations and responsibilities
- **[DESIGN.md](DESIGN.md)** - Design specifications and guidelines
- **[CLAUDE.md](CLAUDE.md)** - Guidance for AI assistants working with this codebase

## Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd "Live STT"

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install dependencies
pip install -e .

# Optional: Install Ollama for LLM refinement
# Download from https://ollama.com
ollama pull gemma4

# Run the application
python -m src.livesttt
```

## Usage

1. **Start the app**: Runs in system tray
2. **Push-to-talk**: Hold the configured hotkey (default: Space) to record
3. **Release to transcribe**: Audio is transcribed and injected into focused window
4. **Cancel**: Press Escape during recording to cancel
5. **Settings**: Right-click tray icon → Settings to configure
   - Push-to-talk hotkey
   - Cancel hotkey
   - LLM model name
   - Enable/disable refinement
   - VAD threshold (speech detection sensitivity)
   - Timeouts

## Prerequisites

- Windows 10+ (64-bit recommended)
- Python 3.10+
- 8GB RAM recommended (4GB minimum without LLM)
- Microphone for speech input
- **ffmpeg** (optional - required for MP3, M4A, FLAC file support)
  - Install via `winget install ffmpeg` or download from https://ffmpeg.org

## Building .exe

```bash
pip install pyinstaller
pyinstaller livesttt.spec
```

## Running Tests

```bash
pytest tests/ -v
```

## License

See [LICENSE](LICENSE) for licensing information.