from unittest.mock import patch, call, MagicMock
from livesttt.injection import injector


def test_inject_copies_text_to_clipboard():
    with patch("pyperclip.copy") as mock_copy, \
         patch("pyautogui.hotkey"), \
         patch("time.sleep"):
        injector.inject("hello world")
    mock_copy.assert_called_once_with("hello world")


def test_inject_sends_ctrl_v():
    with patch("pyperclip.copy"), \
         patch("pyautogui.hotkey") as mock_hotkey, \
         patch("time.sleep"):
        injector.inject("hello world")
    mock_hotkey.assert_called_once_with("ctrl", "v")


def test_inject_sleeps_before_paste():
    sleep_calls = []
    with patch("pyperclip.copy"), \
         patch("pyautogui.hotkey"), \
         patch("time.sleep", side_effect=sleep_calls.append):
        injector.inject("text")
    assert len(sleep_calls) == 1
    assert sleep_calls[0] > 0


def test_inject_empty_string():
    with patch("pyperclip.copy") as mock_copy, \
         patch("pyautogui.hotkey"), \
         patch("time.sleep"):
        injector.inject("")
    mock_copy.assert_called_once_with("")
