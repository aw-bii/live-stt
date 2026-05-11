from unittest.mock import patch, MagicMock
from pathlib import Path


def test_is_ollama_installed_true():
    mock_result = MagicMock()
    mock_result.returncode = 0
    with patch("subprocess.run", return_value=mock_result):
        from bertytype_setup.checks import is_ollama_installed
        assert is_ollama_installed() is True


def test_is_ollama_installed_false_not_found():
    with patch("subprocess.run", side_effect=FileNotFoundError):
        from bertytype_setup import checks
        import importlib
        importlib.reload(checks)
        assert checks.is_ollama_installed() is False


def test_is_ollama_installed_false_nonzero():
    mock_result = MagicMock()
    mock_result.returncode = 1
    with patch("subprocess.run", return_value=mock_result):
        from bertytype_setup import checks
        import importlib
        importlib.reload(checks)
        assert checks.is_ollama_installed() is False


def test_is_model_pulled_true():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"models": [{"name": "gemma4:e2b"}]}
    with patch("requests.get", return_value=mock_resp):
        from bertytype_setup import checks
        import importlib
        importlib.reload(checks)
        assert checks.is_model_pulled("gemma4:e2b") is True


def test_is_model_pulled_false_model_absent():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"models": [{"name": "llama3:latest"}]}
    with patch("requests.get", return_value=mock_resp):
        from bertytype_setup import checks
        import importlib
        importlib.reload(checks)
        assert checks.is_model_pulled("gemma4:e2b") is False


def test_is_model_pulled_false_connection_error():
    import requests
    with patch("requests.get", side_effect=requests.ConnectionError):
        from bertytype_setup import checks
        import importlib
        importlib.reload(checks)
        assert checks.is_model_pulled("gemma4:e2b") is False


def test_is_vibevoice_cached_true(tmp_path):
    model_dir = tmp_path / "models--microsoft--VibeVoice-ASR-HF"
    model_dir.mkdir()
    (model_dir / "model.safetensors").write_bytes(b"fake")
    with patch("bertytype_setup.checks._hf_cache_root", return_value=tmp_path):
        from bertytype_setup import checks
        assert checks.is_vibevoice_cached() is True


def test_is_vibevoice_cached_false_no_dir(tmp_path):
    with patch("bertytype_setup.checks._hf_cache_root", return_value=tmp_path):
        from bertytype_setup import checks
        assert checks.is_vibevoice_cached() is False


def test_check_all_returns_dict():
    with patch("bertytype_setup.checks.is_ollama_installed", return_value=True), \
         patch("bertytype_setup.checks.is_model_pulled", return_value=False), \
         patch("bertytype_setup.checks.is_vibevoice_cached", return_value=False):
        from bertytype_setup import checks
        result = checks.check_all()
    assert result == {"ollama": True, "model": False, "vibevoice": False}
