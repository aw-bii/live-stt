# BertyType - System Architecture

## Overview
BertyType is a modular, offline-first voice dictation application for Windows that processes speech through a pipeline of specialized agents, each responsible for a single concern in the transcription workflow.

## Core Components

### 1. Audio Capture Layer
- **Location**: `src/bertytype/audio/`
- **Responsibilities**:
  - Microphone input via `sounddevice` or `pyaudio`
  - Voice Activity Detection (VAD) for speech detection
  - Audio chunking and buffering for real-time processing
  - File reading for batch transcription mode
- **Key Files**:
  - `capture.py`: Real-time audio capture
  - `vad.py`: Voice activity detection implementation
  - `reader.py`: Audio file reading utilities

### 2. Speech-to-Text (STT) Agent
- **Location**: `src/bertytype/stt/`
- **Responsibilities**:
  - Interface with VibeVoice STT engine
  - Convert audio bytes to text transcripts
  - Handle audio preprocessing for STT
- **Key Files**:
  - `engine.py`: VibeVoice wrapper and STT processing
  - `__init__.py`: Module initialization

### 3. LLM Refinement Agent
- **Location**: `src/bertytype/llm/`
- **Responsibilities**:
  - Communicate with local Gemma 4 model via Ollama
  - Apply text refinement (filler word removal, punctuation, formatting)
  - Support multiple refinement modes (clean-up vs. rewrite)
- **Key Files**:
  - `client.py`: Ollama HTTP client interface
  - `prompts.py`: Refinement prompt templates
  - `__init__.py`: Module initialization

### 4. Text Injection Agent
- **Location**: `src/bertytype/injection/`
- **Responsibilities**:
  - Detect active window on Windows
  - Inject text via clipboard + Ctrl+V simulation
  - Provide fallback direct keystroke injection
  - Export transcripts to files
- **Key Files**:
  - `injector.py`: Text injection mechanisms
  - `exporter.py`: File export functionality
  - `__init__.py`: Module initialization

### 5. Hotkey Management Agent
- **Location**: `src/bertytype/hotkeys/`
- **Responsibilities**:
  - Register global hotkeys (push-to-talk, toggle, cancel)
  - Handle hotkey events and state transitions
  - Provide audio/visual feedback for hotkey states
- **Key Files**:
  - `daemon.py`: Hotkey registration and event handling
  - `__init__.py`: Module initialization

### 6. User Interface Agent
- **Location**: `src/bertytype/ui/`
- **Responsibilities**:
  - System tray icon with context menu
  - Status indicators (recording, processing, ready)
  - Settings window access and management
  - About/help information display
- **Key Files**:
  - `tray.py`: System tray implementation
  - `settings.py`: Settings window and controls
  - `__init__.py`: Module initialization

### 7. Configuration Management
- **Location**: `src/bertytype/config.py`
- **Responsibilities**:
  - Centralized configuration loading/saving
  - Validation of user preferences
  - Default value provision
  - Hot-reload capability when configs change
  - Single source of truth for all user-adjustable parameters

## Data Flow

### Real-time Transcription Flow:
1. **Hotkey Agent** detects keypress → activates audio capture
2. **Audio Capture** processes microphone input → sends audio chunks to STT
3. **STT Agent** converts audio to raw text transcript
4. **LLM Refinement Agent** (if enabled) refines the transcript
5. **Injection Agent** delivers final text to active window
6. **UI Agent** updates status indicators throughout process

### File Transcription Flow:
1. **UI Agent** triggers file transcription request
2. **Audio Capture** reads audio file directly
3. **STT Agent** processes audio to transcript
4. **LLM Refinement Agent** (if enabled) refines transcript
5. **Injection Agent** saves transcript to file and clipboard

## Technical Stack

### Primary Dependencies:
- **Python 3.8+**: Core runtime
- **VibeVoice**: Local speech-to-text engine
- **Ollama**: Local LLM serving (for Gemma 4)
- **sounddevice/pyaudio**: Audio capture
- **pywin32/pygetwindow**: Windows API integration
- **pyperclip/pyautogui**: Text injection mechanisms
- **keyboard**: Global hotkey registration
- **pystray/Pillow**: System tray interface
- **Ollama**: Local LLM API client

### Communication Patterns:
- **Synchronous**: Direct module-to-module calls within same process
- **Event-driven**: Hotkey events triggering audio capture
- **HTTP**: LLM communication with Ollama server (localhost:11434)
- **Shared State**: Configuration object accessed by all agents

## Extensibility Points

### Adding New STT Engines:
1. Create new engine module in `src/bertytype/stt/`
2. Implement standard interface (audio bytes → text)
3. Update factory/selector in STT agent
4. Add configuration options for engine selection

### Adding New Refinement Models:
1. Create new client module in `src/bertytype/llm/`
2. Implement standard interface (text → refined text)
3. Update prompt templates as needed
4. Add model selection to configuration

### Adding New Injection Methods:
1. Create new injector/exporter in `src/bertytype/injection/`
2. Implement standard interface (text → injection result)
3. Update factory/selector in injection agent
4. Add method selection to configuration

## Deployment Architecture

### Local-First Design:
- All processing occurs on-user machine
- No network calls in hot path (except to local Ollama)
- Audio data never leaves local system
- Models stored locally (VibeVoice, Gemma 4 via Ollama)

### Resource Requirements:
- **RAM**: Minimum 4GB (8GB recommended for LLM)
- **Storage**: 2-5GB for models (VibeVoice + Gemma 4)
- **CPU**: Modern multi-core processor for real-time processing
- **OS**: Windows 10+ (64-bit recommended)

## Security & Privacy Considerations

### Data Privacy:
- Audio data processed entirely in-memory
- No audio recordings stored without explicit user action
- Transcripts only persist when user chooses to save
- Local LLM processing prevents data leaving machine

### Security Measures:
- Input validation for all external data (audio files)
- Sandboxed processing where possible
- No automatic network connections beyond local Ollama
- Secure handling of clipboard data

## Performance Characteristics

### Latency Targets:
- Audio capture to STT: <500ms
- STT processing: <1s for typical phrases
- LLM refinement: <2s (depends on phrase length and hardware)
- Text injection: <50ms
- End-to-end: <2s for typical usage

### Resource Usage:
- **Idle**: Minimal CPU (<1%), ~100MB RAM
- **Active STT**: Moderate CPU (20-40%), ~200MB RAM
- **Active LLM**: High CPU usage during processing, ~500MB-1GB RAM
- **Audio buffering**: Configurable, typically 2-5 seconds of audio

## Failure Modes & Recovery

### Graceful Degradation:
- If LLM unavailable: Fall back to raw STT output
- If audio device unavailable: Provide clear error to user
- If injection fails: Offer clipboard copy as fallback
- If configuration invalid: Load safe defaults and notify user

### Error Handling:
- Each agent handles recoverable errors internally
- Unrecoverable errors reported to UI Agent for user notification
- Critical errors trigger safe shutdown procedures
- All errors logged for diagnostic purposes

## Testing Strategy

### Unit Testing:
- Individual module testing with mocked dependencies
- Focus on audio processing, text transformation, injection logic
- Located in `tests/` directory mirroring source structure

### Integration Testing:
- Agent interaction testing
- End-to-end workflow validation
- Configuration change propagation testing

### Manual Testing:
- Real-world usage scenarios
- Different audio environments and accents
- Various target applications for text injection
- Performance benchmarking on target hardware

## Future Enhancement Pathways

### Planned Extensions:
- Multi-language STT support
- Custom vocabulary/domain-specific models
- Voice command system for app control
- Integration with popular IDEs/editors
- Advanced text formatting options

### Architectural Improvements:
- Plugin architecture for third-party extensions
- Improved asynchronous processing pipelines
- Enhanced configuration validation and migration
- Cross-platform expansion (macOS, Linux)