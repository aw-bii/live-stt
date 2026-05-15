from __future__ import annotations
from typing import Callable
from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap, QColor
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from bertytype.ui.tokens import STATUS_COLORS as _STATUS_COLORS

_BAR_HEIGHTS_BY_STATUS: dict[str, list[int]] = {
    "idle":       [16, 32, 48, 32, 16],
    "recording":  [52, 44, 52, 44, 52],
    "processing": [12, 44, 28, 52, 20],
    "error":      [8,  8,  8,  8,  8],
}
_BAR_WIDTH = 8
_BAR_GAP   = 4
_CANVAS    = 64
_ICON_CACHE: dict[str, QIcon] = {}


class _TraySignals(QObject):
    status_changed   = Signal(str)
    notify_requested = Signal(str)


_signals    = _TraySignals()
_tray_icon: QSystemTrayIcon | None = None
_status     = "idle"


def _make_icon(status: str) -> QIcon:
    if status in _ICON_CACHE:
        return _ICON_CACHE[status]
    color_hex  = _STATUS_COLORS.get(status, _STATUS_COLORS["error"])
    bar_heights = _BAR_HEIGHTS_BY_STATUS.get(status, _BAR_HEIGHTS_BY_STATUS["idle"])
    px = QPixmap(_CANVAS, _CANVAS)
    px.fill(Qt.GlobalColor.transparent)
    painter = QPainter(px)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(color_hex))
    painter.setPen(Qt.PenStyle.NoPen)
    total_w = len(bar_heights) * _BAR_WIDTH + (len(bar_heights) - 1) * _BAR_GAP
    x_start = (_CANVAS - total_w) // 2
    for i, bar_h in enumerate(bar_heights):
        x     = x_start + i * (_BAR_WIDTH + _BAR_GAP)
        y_top = (_CANVAS - bar_h) // 2
        painter.drawRoundedRect(x, y_top, _BAR_WIDTH, bar_h, 2, 2)
    painter.end()
    icon = QIcon(px)
    _ICON_CACHE[status] = icon
    return icon


def _on_status_changed(status: str) -> None:
    global _status
    if status == _status:
        return
    _status = status
    if _tray_icon is not None:
        _tray_icon.setIcon(_make_icon(status))


def _on_notify_requested(msg: str) -> None:
    if _tray_icon is not None:
        _tray_icon.showMessage("BertyType", msg)


def set_status(status: str) -> None:
    if status != _status:
        _signals.status_changed.emit(status)


def notify(msg: str) -> None:
    _signals.notify_requested.emit(msg)


def start(
    cfg,
    on_transcribe_file: Callable[[], None],
    on_open_settings: Callable[[], None],
    on_quit: Callable[[], None],
) -> None:
    """Register the tray icon and return immediately (non-blocking)."""
    global _tray_icon
    _signals.status_changed.connect(
        _on_status_changed, Qt.ConnectionType.QueuedConnection
    )
    _signals.notify_requested.connect(
        _on_notify_requested, Qt.ConnectionType.QueuedConnection
    )
    menu = QMenu()
    menu.addAction("Transcribe file...", on_transcribe_file)
    menu.addAction("Settings", on_open_settings)
    menu.addSeparator()
    menu.addAction("Quit", on_quit)
    icon = QSystemTrayIcon()
    icon.setIcon(_make_icon("idle"))
    icon.setToolTip("BertyType")
    icon.setContextMenu(menu)
    icon.show()
    _tray_icon = icon


def stop() -> None:
    global _tray_icon
    if _tray_icon is not None:
        _tray_icon.hide()
        _tray_icon = None
