from typing import Callable
import keyboard


def register(hotkey: str, callback: Callable[[], None]) -> None:
    keyboard.add_hotkey(hotkey, callback)


def register_ptt(
    hotkey: str,
    on_press: Callable[[], None],
    on_release: Callable[[], None],
) -> None:
    keyboard.add_hotkey(hotkey, on_press, suppress=True, trigger_on_release=False)
    keyboard.add_hotkey(hotkey, on_release, suppress=True, trigger_on_release=True)


def stop() -> None:
    keyboard.unhook_all()
