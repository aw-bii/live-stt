# TODO

## Blockers

- [ ] **Install VibeVoice vLLM server** - The STT client (`src/livesttt/stt/vibevoice.py`) expects the VibeVoice vLLM server running at `http://localhost:8000`. Follow the setup guide: https://github.com/microsoft/VibeVoice/blob/main/docs/vibevoice-vllm-asr.md

- [ ] **Install ffmpeg** - Required for MP3, M4A, and FLAC file transcription (WAV works without it). Install via `winget install ffmpeg` then restart the terminal.

## Distribution

- [ ] **Write PyInstaller spec** - Create `livesttt.spec` at the repo root to produce a single-file `.exe` for Windows distribution.

- [ ] **Set up GitHub Actions CI** - Add a workflow that runs `pytest` on push to catch regressions.

## UX / Polish

- [ ] **"Transcript saved" tray notification** - After file transcription completes, show a brief status message (e.g., "Done - transcript saved to foo.txt") before returning to idle.

- [ ] **Hotkey picker in settings** - Replace the plain text field with a key-capture widget: press the combo, it fills in automatically.

- [ ] **Cancel hotkey** - Wire up a hotkey to abort a recording in progress. `hotkeys/daemon.py` has `register()` available; just needs a binding and a call to `_stop_event.set()` in `__main__.py`.
