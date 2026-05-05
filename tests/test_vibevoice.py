import json
from unittest.mock import MagicMock, patch

import pytest

from livesttt.stt import vibevoice


def _make_sse_response(*chunks: str, done: bool = True) -> MagicMock:
    """Build a mock streaming response from SSE content chunks."""
    lines = []
    for chunk in chunks:
        payload = json.dumps({"choices": [{"delta": {"content": chunk}}]})
        lines.append(f"data: {payload}".encode())
    if done:
        lines.append(b"data: [DONE]")
    mock_resp = MagicMock()
    mock_resp.iter_lines.return_value = iter(lines)
    mock_resp.raise_for_status.return_value = None
    return mock_resp


def test_transcribe_returns_assembled_text():
    mock_resp = _make_sse_response("Hello ", "world")
    with patch("livesttt.stt.vibevoice.requests.post", return_value=mock_resp):
        result = vibevoice.transcribe(b"\x00" * 32)
    assert result == "Hello world"


def test_transcribe_strips_whitespace():
    mock_resp = _make_sse_response("  transcript  ")
    with patch("livesttt.stt.vibevoice.requests.post", return_value=mock_resp):
        result = vibevoice.transcribe(b"\x00" * 32)
    assert result == "transcript"


def test_transcribe_handles_vllm_full_text_accumulation():
    # vLLM sometimes sends full accumulated text in each chunk rather than deltas
    mock_resp = _make_sse_response("Hello", "Hello world", "Hello world!")
    with patch("livesttt.stt.vibevoice.requests.post", return_value=mock_resp):
        result = vibevoice.transcribe(b"\x00" * 32)
    assert result == "Hello world!"


def test_transcribe_sends_wav_as_base64():
    mock_resp = _make_sse_response("ok")
    with patch("livesttt.stt.vibevoice.requests.post", return_value=mock_resp) as mock_post:
        vibevoice.transcribe(b"\x00" * 64)
    payload = mock_post.call_args.kwargs["json"]
    audio_url = payload["messages"][1]["content"][0]["audio_url"]["url"]
    assert audio_url.startswith("data:audio/wav;base64,")


def test_transcribe_raises_on_http_error():
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = Exception("503 Service Unavailable")
    with patch("livesttt.stt.vibevoice.requests.post", return_value=mock_resp):
        with pytest.raises(Exception, match="503"):
            vibevoice.transcribe(b"\x00" * 32)


def test_transcribe_skips_malformed_json_lines():
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.iter_lines.return_value = iter([
        b"data: not-json",
        f"data: {json.dumps({'choices': [{'delta': {'content': 'good'}}]})}".encode(),
        b"data: [DONE]",
    ])
    with patch("livesttt.stt.vibevoice.requests.post", return_value=mock_resp):
        result = vibevoice.transcribe(b"\x00" * 32)
    assert result == "good"
