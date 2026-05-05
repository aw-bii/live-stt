from __future__ import annotations
import threading
import tkinter.filedialog
from pathlib import Path

from livesttt import config as cfg_module
from livesttt.audio import capture, vad, reader
from livesttt.stt import engine as stt_engine, vibevoice
from livesttt.llm import client as llm_client
from livesttt.injection import injector, exporter
from livesttt.hotkeys import daemon as hotkey_daemon
from livesttt.ui import tray, settings

_cfg = cfg_module.Config()
_stop_event = threading.Event()


def _on_ptt_press() -> None:
    _stop_event.clear()
    tray.set_status("recording")
    thread = threading.Thread(target=_capture_and_process, daemon=True)
    thread.start()


def _on_ptt_release() -> None:
    _stop_event.set()


def _capture_and_process() -> None:
    audio = capture.start_recording(_stop_event)
    tray.set_status("processing")
    audio = vad.trim_silence(audio, threshold=_cfg.vad_threshold)
    if not audio:
        tray.set_status("idle")
        return
    text = stt_engine.transcribe(audio)
    if _cfg.refine:
        text = llm_client.refine(text, "clean_up", _cfg.model)
    injector.inject(text)
    tray.set_status("idle")


def _on_transcribe_file() -> None:
    path_str = tkinter.filedialog.askopenfilename(
        title="Select audio file",
        filetypes=[("Audio files", "*.wav *.mp3 *.m4a *.flac"), ("All files", "*.*")],
    )
    if not path_str:
        return
    path = Path(path_str)
    tray.set_status("processing")
    audio = reader.read_file(path)
    text = stt_engine.transcribe(audio)
    if _cfg.refine:
        text = llm_client.refine(text, "clean_up", _cfg.model)
    injector.inject(text)
    exporter.save_transcript(text, path)
    tray.set_status("idle")


def _on_open_settings() -> None:
    def _save(updated_cfg: cfg_module.Config) -> None:
        global _cfg
        _cfg = updated_cfg
        cfg_module.save(updated_cfg)

    settings.open_settings(_cfg, on_save=_save)


def _on_quit() -> None:
    hotkey_daemon.stop()
    tray.stop()


def main() -> None:
    global _cfg
    _cfg = cfg_module.load()
    stt_engine.set_backend(vibevoice.transcribe)

    hotkey_daemon.register_ptt(
        _cfg.hotkey.split("+")[-1],
        on_press=_on_ptt_press,
        on_release=_on_ptt_release,
    )

    tray.run(
        cfg=_cfg,
        on_transcribe_file=_on_transcribe_file,
        on_open_settings=_on_open_settings,
        on_quit=_on_quit,
    )


if __name__ == "__main__":
    main()
