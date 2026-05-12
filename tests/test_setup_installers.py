import queue
import threading
import pytest
from unittest.mock import patch, MagicMock, call
from pathlib import Path


def _drain(q: queue.Queue) -> list:
    items = []
    try:
        while True:
            items.append(q.get_nowait())
    except queue.Empty:
        pass
    return items


def test_hf_download_file_passes_hash_to_hub():
    from bertytype_setup import installers
    import importlib
    importlib.reload(installers)
    with patch("huggingface_hub.hf_hub_download") as mock_hub:
        installers._hf_download_file("test/repo", "model.bin", expected_hash="abc123")
        mock_hub.assert_called_once_with(
            repo_id="test/repo",
            filename="model.bin",
            hash="abc123",
        )


def test_hf_download_file_no_hash():
    from bertytype_setup import installers
    import importlib
    importlib.reload(installers)
    with patch("huggingface_hub.hf_hub_download") as mock_hub:
        installers._hf_download_file("test/repo", "model.bin", expected_hash=None)
        mock_hub.assert_called_once_with(
            repo_id="test/repo",
            filename="model.bin",
            hash=None,
        )


def test_download_file_hash_verification_success(tmp_path):
    cancel = threading.Event()
    q = queue.Queue()

    expected_sha256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    content = b""

    def mock_get(*a, **kw):
        resp = MagicMock()
        resp.status_code = 200
        resp.headers = {"content-length": "0"}
        resp.raise_for_status = MagicMock()
        resp.iter_content = lambda chunk_size: iter([content])
        return resp

    dest = tmp_path / "testfile"

    with patch("requests.get", side_effect=mock_get):
        from bertytype_setup import installers
        import importlib
        importlib.reload(installers)
        result = installers._download_file("http://example.com/file", dest, q, cancel, "test", expected_hash=expected_sha256)

    assert result == dest


def test_download_file_hash_verification_mismatch(tmp_path):
    cancel = threading.Event()
    q = queue.Queue()

    expected_sha256 = "wronghash123"

    def mock_get(*a, **kw):
        resp = MagicMock()
        resp.status_code = 200
        resp.headers = {"content-length": "0"}
        resp.raise_for_status = MagicMock()
        resp.iter_content = lambda chunk_size: iter([b"some content"])
        return resp

    dest = tmp_path / "testfile"

    with patch("requests.get", side_effect=mock_get):
        from bertytype_setup import installers
        import importlib
        importlib.reload(installers)
        result = installers._download_file("http://example.com/file", dest, q, cancel, "test", expected_hash=expected_sha256)

    assert result is None


def test_download_file_no_hash_skip_verification(tmp_path):
    cancel = threading.Event()
    q = queue.Queue()

    def mock_get(*a, **kw):
        resp = MagicMock()
        resp.status_code = 200
        resp.headers = {"content-length": "0"}
        resp.raise_for_status = MagicMock()
        resp.iter_content = lambda chunk_size: iter([b"any content"])
        return resp

    dest = tmp_path / "testfile"

    with patch("requests.get", side_effect=mock_get):
        from bertytype_setup import installers
        import importlib
        importlib.reload(installers)
        result = installers._download_file("http://example.com/file", dest, q, cancel, "test", expected_hash=None)

    assert result == dest


def test_download_vibevoice_passes_none_hash():
    cancel = threading.Event()
    q = queue.Queue()

    fake_files = ["config.json"]

    from bertytype_setup import installers
    with patch.object(installers, "_list_hf_files", return_value=fake_files), \
         patch.object(installers, "_hf_download_file") as mock_dl:
        installers.download_vibevoice(q, cancel)

    mock_dl.assert_called_once_with("microsoft/VibeVoice-ASR-HF", "config.json", None)


def test_install_ollama_success(tmp_path):
    cancel = threading.Event()
    q = queue.Queue()

    fake_exe = tmp_path / "OllamaSetup.exe"

    mock_run = MagicMock()
    mock_run.returncode = 0

    with patch("requests.get", return_value=MagicMock(status_code=200)), \
    patch("bertytype_setup.installers._download_file", return_value=fake_exe), \
    patch("subprocess.run", return_value=mock_run):
        from bertytype_setup import installers
        result = installers.install_ollama(q, cancel)

    assert result is True
    events = [item[0] for item in _drain(q)]
    assert "log" in events


def test_install_ollama_download_cancelled(tmp_path):
    cancel = threading.Event()
    cancel.set()
    q = queue.Queue()

    with patch("bertytype_setup.installers._download_file", return_value=None):
        from bertytype_setup import installers
        import importlib
        importlib.reload(installers)
        result = installers.install_ollama(q, cancel)

    assert result is False


def test_ensure_ollama_service_already_running():
    cancel = threading.Event()
    q = queue.Queue()

    mock_resp = MagicMock()
    mock_resp.status_code = 200

    with patch("requests.get", return_value=mock_resp):
        from bertytype_setup import installers
        import importlib
        importlib.reload(installers)
        result = installers._ensure_ollama_service(q, cancel)

    assert result is True


def test_ensure_ollama_service_starts_and_waits():
    cancel = threading.Event()
    q = queue.Queue()

    import requests as req_module
    call_count = [0]

    def mock_get(*a, **kw):
        call_count[0] += 1
        if call_count[0] < 3:
            raise req_module.ConnectionError
        m = MagicMock()
        m.status_code = 200
        return m

    with patch("requests.get", side_effect=mock_get), \
         patch("subprocess.Popen"), \
         patch("time.sleep"):
        from bertytype_setup import installers
        import importlib
        importlib.reload(installers)
        result = installers._ensure_ollama_service(q, cancel)

    assert result is True


def test_pull_model_success():
    cancel = threading.Event()
    q = queue.Queue()

    lines = [
        '{"status":"pulling manifest"}',
        '{"status":"downloading","completed":512,"total":1024}',
        '{"status":"downloading","completed":1024,"total":1024}',
        '{"status":"success"}',
    ]
    mock_proc = MagicMock()
    mock_proc.stdout = iter(lines)
    mock_proc.wait = MagicMock()
    mock_proc.returncode = 0

    with patch("subprocess.Popen", return_value=mock_proc):
        from bertytype_setup import installers
        import importlib
        importlib.reload(installers)
        result = installers.pull_model(q, cancel)

    assert result is True
    events = _drain(q)
    progress_events = [e for e in events if e[0] == "step_progress"]
    assert any(e[2] == pytest.approx(0.5) for e in progress_events)
    assert any(e[2] == pytest.approx(1.0) for e in progress_events)


def test_pull_model_cancelled():
    cancel = threading.Event()
    q = queue.Queue()
    cancel.set()

    mock_proc = MagicMock()
    mock_proc.stdout = iter([])
    mock_proc.wait = MagicMock()
    mock_proc.returncode = 0

    with patch("subprocess.Popen", return_value=mock_proc):
        from bertytype_setup import installers
        import importlib
        importlib.reload(installers)
        result = installers.pull_model(q, cancel)

    assert result is False
    mock_proc.kill.assert_called_once()


def test_pull_model_nonzero_exit():
    cancel = threading.Event()
    q = queue.Queue()

    mock_proc = MagicMock()
    mock_proc.stdout = iter([])
    mock_proc.wait = MagicMock()
    mock_proc.returncode = 1

    with patch("subprocess.Popen", return_value=mock_proc):
        from bertytype_setup import installers
        import importlib
        importlib.reload(installers)
        result = installers.pull_model(q, cancel)

    assert result is False


def test_download_vibevoice_success():
    cancel = threading.Event()
    q = queue.Queue()

    fake_files = ["config.json", "tokenizer.json", "model.safetensors"]

    from bertytype_setup import installers
    with patch.object(installers, "_list_hf_files", return_value=fake_files), \
         patch.object(installers, "_hf_download_file") as mock_dl:
        result = installers.download_vibevoice(q, cancel)

    assert result is True
    assert mock_dl.call_count == 3
    events = _drain(q)
    progress_events = [e for e in events if e[0] == "step_progress" and e[1] == "vibevoice"]
    assert len(progress_events) == 3
    assert progress_events[-1][2] == pytest.approx(1.0)


def test_download_vibevoice_cancelled_between_files():
    cancel = threading.Event()
    q = queue.Queue()

    fake_files = ["config.json", "model.safetensors"]
    call_count = [0]

    def mock_dl(*a, **kw):
        call_count[0] += 1
        if call_count[0] >= 1:
            cancel.set()

    from bertytype_setup import installers
    with patch.object(installers, "_list_hf_files", return_value=fake_files), \
         patch.object(installers, "_hf_download_file", side_effect=mock_dl):
        result = installers.download_vibevoice(q, cancel)

    assert result is False


def test_download_vibevoice_file_fetch_error():
    cancel = threading.Event()
    q = queue.Queue()

    from bertytype_setup import installers
    with patch.object(installers, "_list_hf_files", side_effect=Exception("network error")):
        result = installers.download_vibevoice(q, cancel)

    assert result is False
    events = _drain(q)
    assert any("network error" in str(e) for e in events)


def test_run_all_installs_all_steps():
    cancel = threading.Event()
    q = queue.Queue()

    from bertytype_setup import installers
    with patch.object(installers, "install_ollama", return_value=True) as mock_ol, \
         patch.object(installers, "_ensure_ollama_service", return_value=True), \
         patch.object(installers, "pull_model", return_value=True) as mock_pm, \
         patch.object(installers, "download_vibevoice", return_value=True) as mock_vv:
        installers.run_all_installs(q, cancel, ["ollama", "model", "vibevoice"])

    mock_ol.assert_called_once()
    mock_pm.assert_called_once()
    mock_vv.assert_called_once()
    events = _drain(q)
    assert ("step_done", "ollama") in events
    assert ("step_done", "model") in events
    assert ("step_done", "vibevoice") in events
    assert any(e[0] == "all_done" for e in events)


def test_run_all_installs_model_skipped_if_ollama_failed():
    cancel = threading.Event()
    q = queue.Queue()

    from bertytype_setup import installers
    with patch.object(installers, "install_ollama", return_value=False), \
         patch.object(installers, "pull_model") as mock_pm, \
         patch.object(installers, "download_vibevoice", return_value=True):
        installers.run_all_installs(q, cancel, ["ollama", "model", "vibevoice"])

    mock_pm.assert_not_called()
    events = _drain(q)
    assert ("step_failed", "ollama") in events
    assert ("step_skipped", "model") in events


def test_run_all_installs_only_vibevoice():
    cancel = threading.Event()
    q = queue.Queue()

    from bertytype_setup import installers
    with patch.object(installers, "install_ollama") as mock_ol, \
         patch.object(installers, "_ensure_ollama_service", return_value=True), \
         patch.object(installers, "pull_model") as mock_pm, \
         patch.object(installers, "download_vibevoice", return_value=True):
        installers.run_all_installs(q, cancel, ["vibevoice"])

    mock_ol.assert_not_called()
    mock_pm.assert_not_called()


def test_run_all_installs_model_only_ensures_service():
    cancel = threading.Event()
    q = queue.Queue()

    from bertytype_setup import installers
    with patch.object(installers, "install_ollama") as mock_ol, \
         patch.object(installers, "_ensure_ollama_service", return_value=True) as mock_svc, \
         patch.object(installers, "pull_model", return_value=True):
        installers.run_all_installs(q, cancel, ["model"])

    mock_ol.assert_not_called()
    mock_svc.assert_called_once()
