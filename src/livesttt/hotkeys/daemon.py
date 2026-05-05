from typing import Callable
import keyboard


def register(hotkey: str, callback: Callable[[], None]) -> None:
    keyboard.add_hotkey(hotkey, callback)


def register_ptt(
    key: str,
    on_press: Callable[[], None],
    on_release: Callable[[], None],
) -> None:
    keyboard.on_press_key(key, lambda _: on_press(), suppress=True)
    keyboard.on_release_key(key, lambda _: on_release(), suppress=True)


def stop() -> None:
    keyboard.unhook_all()
