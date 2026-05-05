from unittest.mock import patch, MagicMock, call
from livesttt.hotkeys import daemon


def test_register_calls_keyboard_add_hotkey():
    cb = MagicMock()
    with patch("keyboard.add_hotkey") as mock_add:
        daemon.register("ctrl+shift+space", cb)
    mock_add.assert_called_once_with("ctrl+shift+space", cb)


def test_register_ptt_hooks_press_and_release():
    on_press = MagicMock()
    on_release = MagicMock()
    with patch("keyboard.on_press_key") as mock_press, \
         patch("keyboard.on_release_key") as mock_release:
        daemon.register_ptt("f9", on_press, on_release)
    assert mock_press.call_count == 1
    assert mock_release.call_count == 1


def test_stop_unhooks_all():
    with patch("keyboard.unhook_all") as mock_unhook:
        daemon.stop()
    mock_unhook.assert_called_once()
