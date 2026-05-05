# TODO

## Blockers

- [x] **VibeVoice integration** - Now supports both local (Transformers) and HTTP (vLLM) backends. Local is preferred, falls back to HTTP.

- [x] **Install ffmpeg** - Added to README prerequisites (optional - for MP3/M4A/FLAC)

## Distribution

- [x] **PyInstaller spec** - Created `livesttt.spec` at the repo root for .exe build

- [x] **GitHub Actions CI** - Created `.github/workflows/ci.yml` that runs pytest on push/PR

## UX / Polish

- [x] **"Transcript saved" tray notification** - Implemented in `__main__.py` with `messages.INFO_TRANSCRIPTION_COMPLETE`

- [x] **Hotkey picker in settings** - Enhanced with key capture, cancel hotkey, and timeout settings

- [x] **Cancel hotkey** - Implemented with Escape key by default. Press during recording to abort.

## All Items Complete!
