# AGENTS.md - Agent Configurations for Live STT

This file provides guidance for AI coding agents working on the Live STT repository. Following these guidelines will help ensure smooth development experiences.

## 1. Use the Development Server, **not** `pip install` during active sessions

* **Always work within the activated `.venv`** while iterating on the application.  
* **Do _not_ run `pip install` inside the agent session** unless adding new dependencies.  
* If you add or update dependencies:
  1. Update `pyproject.toml`
  2. Re-install with `pip install -e .`  
  3. Restart any running application instances

## 2. Useful Commands

| Command | Purpose |
|---------|---------|
| `python -m src.livesttt` | Run the Live STT application |
| `pytest tests/` | Execute the test suite |
| `pip install -e .` | Reinstall package in development mode after changes |
| `python -m pytest tests/ -v` | Run tests with verbose output |
| `graphify update .` | Update the knowledge graph after code changes |

## 3. Project Structure

```
Live STT/
├── src/livesttt/          # Main source code
│   ├── audio/             # Audio capture and VAD
│   ├── stt/               # Speech-to-text processing
│   ├── llm/               # LLM refinement via Ollama
│   ├── injection/         # Text injection and export
│   ├── hotkeys/           # Global hotkey management
│   ├── ui/                # System tray and settings
│   ├── config.py          # Centralized configuration
│   ├── __main__.py        # Application entry point
│   └── __init__.py        # Package initializer
├── tests/                 # Test suite
├── docs/                  # Additional documentation
├── graphify-out/          # Knowledge graph for codebase understanding
├── PRODUCT.md             # Product requirements and vision
├── ARCHITECTURE.md        # System architecture
├── DESIGN.md              # Design specifications
└── pyproject.toml         # Project dependencies and metadata
```

## 4. Coding Conventions

* **Python Style** - Follow PEP 8 guidelines
* **Type Hints** - Use type annotations for function signatures where practical
* **Module Organization** - Each agent responsibility has its own module under `src/livesttt/`
* **Error Handling** - Handle exceptions gracefully and provide meaningful error messages
* **Documentation** - Include docstrings for public functions and classes

## 5. Agent-Specific Guidelines

When working on specific agents, consider these responsibilities:

### STT Agent (`src/livesttt/stt/`)
- Focus on audio processing accuracy and efficiency
- Maintain clean separation between audio capture and STT processing
- Ensure proper resource cleanup (audio streams, etc.)

### LLM Refinement Agent (`src/livesttt/llm/`)
- Keep prompts modular and testable
- Handle Ollama connection failures gracefully
- Support easy switching between different LLM backends

### Injection Agent (`src/livesttt/injection/`)
- Test injection across different applications (Notepad, VS Code, browsers, etc.)
- Provide fallback mechanisms when primary injection fails
- Respect user privacy and system security boundaries

### Hotkey Agent (`src/livesttt/hotkeys/`)
- Ensure hotkeys don't conflict with common system shortcuts
- Provide clear visual/audio feedback for hotkey states
- Handle edge cases like rapid key presses

### UI Agent (`src/livesttt/ui/`)
- Keep the system tray interface lightweight and responsive
- Ensure settings window is intuitive and accessible
- Provide clear status indicators for all application states

### Config Agent (`src/livesttt/config.py`)
- Maintain backward compatibility when updating config schema
- Provide sensible defaults for all configuration options
- Validate configuration values at load time

## 6. Common Tasks

### Adding a New Feature
1. Identify which agent(s) will be affected
2. Update the relevant module(s) in `src/livesttt/`
3. Add or modify configuration options in `config.py` if needed
4. Update tests in `tests/` to cover new functionality
5. Update documentation if the feature affects user-facing behavior

### Modifying Existing Functionality
1. Locate the relevant agent module
2. Make minimal, focused changes
3. Ensure existing tests still pass
4. Add tests for any new behavior
5. Verify integration with other agents still works correctly

## 7. Troubleshooting

### Application Won't Start
- Check that the virtual environment is activated
- Verify all dependencies are installed with `pip list`
- Confirm Ollama is running if using LLM refinement (`ollama run gemma4 "test"`)
- Check audio device permissions and availability

### Text Not Injecting
- Verify active window detection is working
- Check clipboard functionality
- Try alternative injection methods in config
- Look for security software blocking input simulation

### Poor Transcription Quality
- Adjust VAD threshold in configuration
- Check microphone quality and positioning
- Consider environment noise levels
- Verify audio sample rate matches STT expectations

## 8. Getting Help

- Refer to `ARCHITECTURE.md` for system design details
- Consult `PRODUCT.md` for feature vision and user stories
- Check `DESIGN.md` for UI/UX guidelines
- Use the graphify knowledge graph: `graphify explain "<concept>"`
- Run `pytest tests/ -v` to see which tests are failing