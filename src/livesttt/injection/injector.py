import time
import pyperclip
import pyautogui

_PASTE_DELAY = 0.05


def inject(text: str) -> None:
    pyperclip.copy(text)
    time.sleep(_PASTE_DELAY)
    pyautogui.hotkey("ctrl", "v")
