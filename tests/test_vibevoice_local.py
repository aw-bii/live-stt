import pytest
from unittest.mock import patch, MagicMock

from livesttt.stt import vibevoice_local


def test_is_available_returns_false_when_import_fails():
    with patch.dict("sys.modules", {"transformers": None}):
        result = vibevoice_local.is_available()
    assert result is False


def test_is_available_returns_true_when_model_loads():
    mock_processor = MagicMock()
    mock_model = MagicMock()
    with patch("transformers.AutoProcessor") as mock_proc_cls, \
         patch("transformers.VibeVoiceAsrForConditionalGeneration") as mock_model_cls:
        mock_proc_cls.from_pretrained.return_value = mock_processor
        mock_model_cls.from_pretrained.return_value = mock_model
        result = vibevoice_local.is_available()
    assert result is True