from __future__ import annotations
from typing import Callable
import pystray
from PIL import Image, ImageDraw

_icon: pystray.Icon | None = None
_status = "idle"
_STATUS_COLORS = {"idle": "green", "recording": "red", "processing": "orange"}


def _make_icon(color: str) -> Image.Image:
    img = Image.new("RGB", (64, 64), color="black")
    draw = ImageDraw.Draw(img)
    draw.ellipse([8, 8, 56, 56], fill=color)
    return img


def set_status(status: str) -> None:
    global _status
    _status = status
    if _icon:
        _icon.icon = _make_icon(_STATUS_COLORS.get(status, "gray"))


def run(
    cfg,
    on_transcribe_file: Callable[[], None],
    on_open_settings: Callable[[], None],
    on_quit: Callable[[], None],
) -> None:
    global _icon

    menu = pystray.Menu(
        pystray.MenuItem("Transcribe file...", lambda icon, item: on_transcribe_file()),
        pystray.MenuItem("Settings", lambda icon, item: on_open_settings()),
        pystray.MenuItem("Quit", lambda icon, item: on_quit()),
    )
    _icon = pystray.Icon("livesttt", _make_icon("green"), "live-stt", menu)
    _icon.run()


def stop() -> None:
    if _icon:
        _icon.stop()
