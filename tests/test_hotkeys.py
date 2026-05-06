from unittest.mock import patch, MagicMock, call
from livesttt.hotkeys import daemon


def test_register_calls_keyboard_add_hotkey():
    cb = MagicMock()
    with patch("keyboard.add_hotkey") as mock_add:
        daemon.register("ctrl+shift+space", cb)
    mock_add.assert_called_once_with("ctrl+shift+space", cb)


def test_register_ptt_hooks_press_and_release_with_full_combo():
    on_press = MagicMock()
    on_release = MagicMock()
    with patch("keyboard.add_hotkey") as mock_add:
        daemon.register_ptt("ctrl+shift+space", on_press, on_release)
    assert mock_add.call_count == 2
    calls = mock_add.call_args_list
    assert calls[0][0][0] == "ctrl+shift+space"
    assert calls[0][0][1] == on_press
    assert calls[0][1]["suppress"] is True
    assert calls[0][1]["trigger_on_release"] is False
    assert calls[1][0][0] == "ctrl+shift+space"
    assert calls[1][0][1] == on_release
    assert calls[1][1]["suppress"] is True
    assert calls[1][1]["trigger_on_release"] is True


def test_stop_unhooks_all():
    with patch("keyboard.unhook_all") as mock_unhook:
        daemon.stop()
    mock_unhook.assert_called_once()
