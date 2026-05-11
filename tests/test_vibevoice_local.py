import pytest
from unittest.mock import patch, MagicMock

from livesttt.stt import vibevoice_local


def test_is_available_returns_false_when_import_fails():
    with patch.dict("sys.modules", {"transformers": None}):
        result = vibevoice_local.is_available()
    assert result is False


def test_is_available_returns_true_when_transformers_importable():
    with patch.dict("sys.modules", {"transformers": MagicMock()}):
        result = vibevoice_local.is_available()
    assert result is True
