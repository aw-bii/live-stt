from __future__ import annotations
import json
import queue
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from typing import Optional

import requests

OLLAMA_DOWNLOAD_URL = "https://ollama.com/download/OllamaSetup.exe"
OLLAMA_API = "http://localhost:11434"
MODEL = "gemma4:e2b"
VIBEVOICE_REPO = "microsoft/VibeVoice-ASR-HF"


def _post(q: queue.Queue, event: str, *args) -> None:
    q.put((event, *args))


def _download_file(
    url: str,
    dest: Path,
    q: queue.Queue,
    cancel: threading.Event,
    step_key: str,
) -> Optional[Path]:
    """Stream-download url to dest. Returns dest on success, None on cancel/error."""
    tmp = dest.with_suffix(".tmp")
    try:
        with requests.get(url, stream=True, timeout=30) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0))
            downloaded = 0
            with open(tmp, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    if cancel.is_set():
                        tmp.unlink(missing_ok=True)
                        return None
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        _post(q, "step_progress", step_key, downloaded / total)
        tmp.rename(dest)
        return dest
    except Exception as e:
        tmp.unlink(missing_ok=True)
        _post(q, "log", f"Download failed: {e}")
        return None


def _ensure_ollama_service(q: queue.Queue, cancel: threading.Event) -> bool:
    """Start ollama serve if not already running. Poll up to 30s."""
    try:
        if requests.get(f"{OLLAMA_API}/api/tags", timeout=2).status_code == 200:
            return True
    except Exception:
        pass
    _post(q, "log", "Starting Ollama service...")
    subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(30):
        if cancel.is_set():
            return False
        time.sleep(1)
        try:
            if requests.get(f"{OLLAMA_API}/api/tags", timeout=2).status_code == 200:
                return True
        except Exception:
            pass
    _post(q, "log", "Ollama service did not start within 30s")
    return False


def install_ollama(q: queue.Queue, cancel: threading.Event) -> bool:
    """Download OllamaSetup.exe, run silently, then ensure service is up."""
    if cancel.is_set():
        return False
    _post(q, "log", "Downloading Ollama installer...")
    tmp_dir = Path(tempfile.gettempdir())
    dest = tmp_dir / "OllamaSetup.exe"
    path = _download_file(OLLAMA_DOWNLOAD_URL, dest, q, cancel, "ollama")
    if path is None:
        return False
    _post(q, "log", "Running Ollama installer (this may take a minute)...")
    result = subprocess.run([str(path), "/SILENT"], timeout=180)
    path.unlink(missing_ok=True)
    if result.returncode != 0:
        _post(q, "log", f"Installer exited with code {result.returncode}")
        return False
    return _ensure_ollama_service(q, cancel)


def pull_model(q: queue.Queue, cancel: threading.Event, model: str = MODEL) -> bool:
    """Stream `ollama pull <model>` and report progress."""
    _post(q, "log", f"Pulling {model} (this may take several minutes)...")
    try:
        proc = subprocess.Popen(
            ["ollama", "pull", model],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if cancel.is_set():
            proc.kill()
            return False
        for line in proc.stdout:
            if cancel.is_set():
                proc.kill()
                return False
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                total = data.get("total", 0)
                completed = data.get("completed", 0)
                status = data.get("status", "")
                if total and completed:
                    _post(q, "step_progress", "model", completed / total)
                if status:
                    _post(q, "log", status)
            except json.JSONDecodeError:
                _post(q, "log", line)
        proc.wait()
        return proc.returncode == 0
    except Exception as e:
        _post(q, "log", f"Model pull failed: {e}")
        return False


def _list_hf_files(repo_id: str) -> list[str]:
    from huggingface_hub import list_repo_files
    return list(list_repo_files(repo_id))


def _hf_download_file(repo_id: str, filename: str) -> None:
    from huggingface_hub import hf_hub_download
    hf_hub_download(repo_id=repo_id, filename=filename)


def download_vibevoice(q: queue.Queue, cancel: threading.Event) -> bool:
    """Download VibeVoice ASR model files to the HuggingFace cache."""
    if cancel.is_set():
        return False
    _post(q, "log", "Fetching VibeVoice file list from Hugging Face...")
    try:
        files = _list_hf_files(VIBEVOICE_REPO)
    except Exception as e:
        _post(q, "log", f"Failed to fetch file list: {e}")
        return False

    total = len(files)
    for i, filename in enumerate(files):
        if cancel.is_set():
            return False
        _post(q, "log", f"Downloading {filename} ({i + 1}/{total})...")
        try:
            _hf_download_file(VIBEVOICE_REPO, filename)
        except Exception as e:
            _post(q, "log", f"Failed to download {filename}: {e}")
            return False
        _post(q, "step_progress", "vibevoice", (i + 1) / total)

    return True
