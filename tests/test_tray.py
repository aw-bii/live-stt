from unittest.mock import MagicMock
import bertytype.ui.tray as tray_module


def test_notify_calls_icon_notify(monkeypatch):
    mock_icon = MagicMock()
    monkeypatch.setattr(tray_module, "_icon", mock_icon)
    tray_module.notify("Done - saved to foo.txt")
    mock_icon.notify.assert_called_once_with("Done - saved to foo.txt", "BertyType")


def test_notify_is_no_op_when_no_icon(monkeypatch):
    monkeypatch.setattr(tray_module, "_icon", None)
    tray_module.notify("any message")  # must not raise
