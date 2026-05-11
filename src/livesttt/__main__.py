from __future__ import annotations
import threading
import tkinter.filedialog
from pathlib import Path
import requests

from livesttt import config as cfg_module
from livesttt.audio import capture, vad, reader
from livesttt.stt import engine as stt_engine, vibevoice, vibevoice_local
from livesttt.llm import client as llm_client
from livesttt.injection import injector, exporter
from livesttt.hotkeys import daemon as hotkey_daemon
from livesttt.ui import tray, settings
from livesttt import messages
from livesttt import logging as log_module

logger = log_module.logger

_cfg = cfg_module.Config()
_stop_event = threading.Event()
_cancel_event = threading.Event()
_quit_event = threading.Event()
_health = {"vibevoice": False, "ollama": False}
_health_lock = threading.Lock()


def _on_ptt_press() -> None:
    _cancel_event.clear()
    _stop_event.clear()
    tray.set_status("recording")
    thread = threading.Thread(target=_capture_and_process, daemon=True)
    thread.start()


def _on_ptt_release() -> None:
    _stop_event.set()


def _on_cancel() -> None:
    _cancel_event.set()
    _stop_event.set()


def _capture_and_process() -> None:
    with _health_lock:
        health = _health.copy()
    try:
        audio = capture.start_recording(_stop_event)
        if _cancel_event.is_set():
            tray.set_status("idle")
            return
        tray.set_status("processing")
        audio = vad.trim_silence(audio, threshold=_cfg.vad_threshold)
        if not audio:
            tray.set_status("idle")
            return
        text = stt_engine.transcribe(audio)
        if _cfg.refine and health["ollama"]:
            try:
                future = llm_client.refine_async(text, "clean_up", _cfg.model, _cfg.llm_timeout)
                text = future.result(timeout=_cfg.llm_timeout + 5)
            except requests.ConnectionError as e:
                logger.warning(f"LLM refinement failed: {e}")
                tray.notify(messages.ERROR_OLLAMA_UNAVAILABLE)
            except TimeoutError as e:
                logger.warning(f"LLM refinement timed out: {e}")
                tray.notify(messages.ERROR_OLLAMA_UNAVAILABLE)
            except Exception as e:
                logger.warning(f"LLM refinement failed: {e}")
                tray.notify(messages.ERROR_OLLAMA_UNAVAILABLE)
        elif _cfg.refine and not health["ollama"]:
            logger.info("Skipping refinement - Ollama unavailable")
        try:
            injector.inject(text, _cfg.injection_delay)
        except Exception as e:
            logger.warning(f"Injection failed: {e}")
            pyperclip = __import__("pyperclip")
            pyperclip.copy(text)
            tray.notify(messages.ERROR_INJECTION_FAILED)
        tray.set_status("idle")
    except (requests.ConnectionError, requests.Timeout) as e:
        logger.error(f"VibeVoice unavailable: {e}")
        tray.set_status("error")
        tray.notify(messages.ERROR_VIBEVOICE_UNAVAILABLE)
    except Exception as e:
        logger.exception(f"Transcription failed: {e}")
        tray.set_status("error")
        tray.notify(messages.ERROR_TRANSCRIPTION_FAILED)


def _on_transcribe_file() -> None:
    path_str = tkinter.filedialog.askopenfilename(
        title="Select audio file",
        filetypes=[("Audio files", "*.wav *.mp3 *.m4a *.flac"), ("All files", "*.*")],
    )
    if not path_str:
        return
    with _health_lock:
        health = _health.copy()
    try:
        path = Path(path_str)
        tray.set_status("processing")
        audio = reader.read_file(path)
        if not audio:
            tray.set_status("error")
            tray.notify(messages.ERROR_FILE_READ_FAILED)
            return
        text = stt_engine.transcribe(audio)
        if _cfg.refine and health["ollama"]:
            try:
                future = llm_client.refine_async(text, "clean_up", _cfg.model, _cfg.llm_timeout)
                text = future.result(timeout=_cfg.llm_timeout + 5)
            except Exception as e:
                logger.warning(f"LLM refinement failed: {e}")
        elif _cfg.refine and not health["ollama"]:
            logger.info("Skipping refinement - Ollama unavailable")
        try:
            injector.inject(text, _cfg.injection_delay)
        except Exception as e:
            logger.warning(f"Injection failed: {e}")
            pyperclip = __import__("pyperclip")
            pyperclip.copy(text)
            tray.notify(messages.ERROR_INJECTION_FAILED)
        out_path = exporter.save_transcript(text, path)
        tray.notify(messages.INFO_TRANSCRIPTION_COMPLETE)
        tray.set_status("idle")
    except (requests.ConnectionError, requests.Timeout) as e:
        logger.error(f"VibeVoice unavailable: {e}")
        tray.set_status("error")
        tray.notify(messages.ERROR_VIBEVOICE_UNAVAILABLE)
    except Exception as e:
        logger.exception(f"File transcription failed: {e}")
        tray.set_status("error")
        tray.notify(messages.ERROR_TRANSCRIPTION_FAILED)


def _on_open_settings() -> None:
    def _save(updated_cfg: cfg_module.Config) -> None:
        global _cfg
        _cfg = updated_cfg
        cfg_module.save(updated_cfg)

    settings.open_settings(_cfg, on_save=_save)


def _on_quit() -> None:
    _quit_event.set()
    llm_client.shutdown()
    hotkey_daemon.stop()
    tray.stop()


def _check_health() -> dict[str, bool]:
    health = {"vibevoice": False, "ollama": False}
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        health["ollama"] = resp.status_code == 200
    except (requests.ConnectionError, requests.Timeout):
        health["ollama"] = False
    if vibevoice_local.is_available():
        health["vibevoice"] = True
    else:
        try:
            resp = requests.get("http://localhost:8000/v1/models", timeout=5)
            health["vibevoice"] = resp.status_code == 200
        except (requests.ConnectionError, requests.Timeout):
            health["vibevoice"] = False
    return health


def _periodic_health_check(interval: int = 60) -> None:
    global _health
    while not _quit_event.is_set():
        new_health = _check_health()
        logger.debug(f"Periodic health: vibevoice={new_health['vibevoice']}, ollama={new_health['ollama']}")
        with _health_lock:
            _health = new_health
        _quit_event.wait(interval)


def main() -> None:
    global _cfg, _health
    _cfg = cfg_module.load()

    if vibevoice_local.is_available():
        stt_engine.set_backend(vibevoice_local.transcribe)
        logger.info("Using local VibeVoice (Transformers)")
    else:
        stt_engine.set_backend(vibevoice.transcribe)
        logger.info("Using HTTP VibeVoice (vLLM)")

    _health = _check_health()

    if not _health["vibevoice"] and not vibevoice_local.is_available():
        logger.warning("VibeVoice not available at startup")
    if not _health["ollama"] and _cfg.refine:
        logger.warning("Ollama not available - refinement disabled")

    monitor_thread = threading.Thread(target=_periodic_health_check, daemon=True)
    monitor_thread.start()

    hotkey_daemon.register_ptt(
        _cfg.hotkey,
        on_press=_on_ptt_press,
        on_release=_on_ptt_release,
    )
    hotkey_daemon.register(_cfg.cancel_hotkey, _on_cancel)

    tray.run(
        cfg=_cfg,
        on_transcribe_file=_on_transcribe_file,
        on_open_settings=_on_open_settings,
        on_quit=_on_quit,
    )


if __name__ == "__main__":
    main()


