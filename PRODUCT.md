# BertyType - Product Requirements Document

## Vision
A local, offline voice-dictation app that provides real-time speech-to-text transcription with optional LLM refinement, enabling users to dictate text into any application without cloud dependencies.

## Target Users
- Professionals who need hands-free text input
- Writers and content creators
- Individuals with accessibility needs
- Privacy-conscious users who prefer local processing
- Developers wanting voice-controlled coding assistance

## Core Features
1. **Real-time Speech Recognition**
   - Push-to-talk or toggle recording modes
   - Local STT using VibeVoice engine
   - Voice activity detection for automatic start/stop

2. **Text Refinement (Optional)**
   - Local LLM processing via Gemma 4 (Ollama)
   - Filler word removal
   - Punctuation and formatting correction
   - Context-aware rewriting

3. **System-Wide Text Injection**
   - Active window detection
   - Clipboard-based text injection with Ctrl+V simulation
   - Direct keystroke injection fallback

4. **File Transcription**
   - Transcribe existing audio files
   - Save transcripts alongside source files
   - Support for common audio formats

5. **User Configuration**
   - Customizable hotkeys
   - Model selection and tuning
   - VAD sensitivity adjustment
   - Refinement toggle

## User Stories
### As a user, I want to:
- Hold a hotkey to record speech and release to transcribe
- Toggle recording on/off with a hotkey for continuous dictation
- See visual feedback when recording is active
- Have transcribed text appear in my currently focused application
- Optionally refine transcriptions for clarity and correctness
- Transcribe existing audio files from my computer
- Configure the hotkey to suit my workflow
- Use the app without internet connectivity
- Keep my voice data private and local

### As a power user, I want to:
- Create custom voice commands for frequent text snippets
- Integrate with my IDE for voice-controlled coding
- Process multiple audio files in batch
- Adjust STT accuracy vs. speed tradeoffs
- View transcription history and edit past results

## Success Criteria
- Accuracy: >90% transcription accuracy for clear speech in quiet environments
- Latency: <2 second delay from speech completion to text insertion
- Privacy: No audio or text leaves the local machine
- Reliability: Stable operation across Windows versions
- Usability: Intuitive hotkey system requiring minimal learning curve
- Performance: Minimal CPU/memory usage during idle state

## Non-Features (Out of Scope)
- Cloud-based processing alternatives
- Mobile applications (iOS/Android)
- Real-time translation capabilities
- Speaker identification/diarization
- Emotion or sentiment analysis

## Technical Constraints
- Windows-only initial release
- Requires Ollama running locally for LLM features
- Python 3.8+ runtime
- Minimum 4GB RAM recommended
- SSD storage preferred for model files