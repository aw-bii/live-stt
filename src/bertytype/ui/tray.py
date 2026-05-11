from __future__ import annotations
from typing import Callable
import pystray
from PIL import Image, ImageDraw

_icon: pystray.Icon | None = None
_status = "idle"
_STATUS_COLORS = {
    "idle": "#4CAF50",
    "recording": "#F44336",
    "processing": "#FF9800",
    "error": "#9E9E9E",
}

_BAR_HEIGHTS = [16, 32, 48, 32, 16]
_BAR_WIDTH = 8
_BAR_GAP = 4
_CANVAS = 64
_ICON_CACHE: dict[str, Image.Image] = {}


def _make_icon(color: str) -> Image.Image:
    if color in _ICON_CACHE:
        return _ICON_CACHE[color]
    img = Image.new("RGBA", (_CANVAS, _CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    total_width = len(_BAR_HEIGHTS) * _BAR_WIDTH + (len(_BAR_HEIGHTS) - 1) * _BAR_GAP
    x_start = (_CANVAS - total_width) // 2
    for i, bar_h in enumerate(_BAR_HEIGHTS):
        x = x_start + i * (_BAR_WIDTH + _BAR_GAP)
        y_top = (_CANVAS - bar_h) // 2
        y_bot = y_top + bar_h
        draw.rounded_rectangle([x, y_top, x + _BAR_WIDTH, y_bot], radius=2, fill=color)
    _ICON_CACHE[color] = img
    return img


def set_status(status: str) -> None:
    global _status
    if status == _status:
        return
    _status = status
    if _icon:
        _icon.icon = _make_icon(_STATUS_COLORS.get(status, _STATUS_COLORS["error"]))


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
    _icon = pystray.Icon("bertytype", _make_icon(_STATUS_COLORS["idle"]), "live-stt", menu)
    _icon.run()


def notify(message: str) -> None:
    if _icon:
        _icon.notify(message, "live-stt")


def stop() -> None:
    if _icon:
        _icon.stop()
