import bertytype.ui.tray as tray_module


def test_notify_emits_signal(qapp):
    received = []
    tray_module._signals.notify_requested.connect(received.append)
    try:
        tray_module.notify("Done - saved to foo.txt")
        assert "Done - saved to foo.txt" in received
    finally:
        tray_module._signals.notify_requested.disconnect(received.append)


def test_set_status_emits_signal(qapp):
    received = []
    tray_module._signals.status_changed.connect(received.append)
    try:
        original = tray_module._status
        tray_module._status = "idle"
        tray_module.set_status("recording")
        assert "recording" in received
    finally:
        tray_module._status = original
        tray_module._signals.status_changed.disconnect(received.append)


def test_set_status_dedup_does_not_emit(qapp):
    received = []
    tray_module._signals.status_changed.connect(received.append)
    try:
        tray_module._status = "idle"
        tray_module.set_status("idle")
        assert received == []
    finally:
        tray_module._signals.status_changed.disconnect(received.append)


def test_notify_no_crash_without_tray_icon(qapp):
    original = tray_module._tray_icon
    tray_module._tray_icon = None
    try:
        tray_module.notify("any message")  # must not raise
    finally:
        tray_module._tray_icon = original


def test_set_status_no_crash_without_tray_icon(qapp):
    from bertytype.ui import tray as tray_module_local
    from PySide6.QtCore import QCoreApplication
    original = tray_module_local._status
    try:
        tray_module_local._status = "idle"
        tray_module_local.set_status("recording")  # must not raise
        QCoreApplication.processEvents()
    finally:
        tray_module_local._status = original
