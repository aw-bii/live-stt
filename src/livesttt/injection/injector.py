import time
import pyperclip
import pyautogui


def inject(text: str, delay: float = 0.05) -> None:
    pyperclip.copy(text)
    time.sleep(delay)
    pyautogui.hotkey("ctrl", "v")
