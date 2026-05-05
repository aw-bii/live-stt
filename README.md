# Live STT

A local, offline voice-dictation app for Windows that provides real-time speech-to-text transcription with optional LLM refinement.

## Overview

Live STT captures microphone audio, transcribes speech using VibeVoice (local STT), optionally refines the text with Gemma 4 (local LLM via Ollama), and injects the result into whatever window the user has focused - all without any cloud dependency.

## Features

- **Real-time Speech Recognition**: Push-to-talk or toggle recording modes
- **Local Processing**: All audio and text processing happens on your machine
- **Optional LLM Refinement**: Improve transcriptions with Gemma 4 via Ollama
- **System-wide Injection**: Works in any application via clipboard + Ctrl+V
- **File Transcription**: Transcribe existing audio files
- **Customizable Hotkeys**: Tailor the workflow to your preferences
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
cd Live STT

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install dependencies
pip install -e .

# Install and run Ollama (separately)
# Download from https://ollama.com
ollama pull gemma4

# Run the application
python -m src.livesttt
```

## Prerequisites

- Windows 10+ (64-bit recommended)
- Python 3.8+
- Ollama running locally (for LLM refinement features)
- Microphone for speech input

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

See [LICENSE](LICENSE) for licensing information.