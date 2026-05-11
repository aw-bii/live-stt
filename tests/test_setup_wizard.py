import queue
import threading
from unittest.mock import MagicMock, patch


def _make_wizard_no_tk():
    """Construct a Wizard bypassing tkinter initialisation."""
    with patch("tkinter.Tk"):
        from bertytype_setup import wizard as wiz_mod
        import importlib
        importlib.reload(wiz_mod)
        w = wiz_mod.Wizard.__new__(wiz_mod.Wizard)
        w._queue = queue.Queue()
        w._cancel = threading.Event()
        w._failures = []
        w._steps_to_install = []
        w._check_results = {}
        w._root = MagicMock()
        w._current_frame = None
        w._install_frame = MagicMock()
        w._show_finish = MagicMock()
        return w


def test_poll_queue_dispatches_log():
    w = _make_wizard_no_tk()
    w._queue.put(("log", "hello world"))
    w._queue.put(("all_done", {}))
    w._poll_queue()
    w._install_frame.log.assert_called_with("hello world")
    w._show_finish.assert_called_once_with([])


def test_poll_queue_dispatches_step_done():
    w = _make_wizard_no_tk()
    w._queue.put(("step_done", "ollama"))
    w._queue.put(("all_done", {}))
    w._poll_queue()
    w._install_frame.step_done.assert_called_with("ollama")


def test_poll_queue_dispatches_step_failed_records_failure():
    w = _make_wizard_no_tk()
    w._queue.put(("step_failed", "model"))
    w._queue.put(("all_done", {}))
    w._poll_queue()
    w._install_frame.step_failed.assert_called_with("model")
    assert "model" in w._failures
    w._show_finish.assert_called_once_with(["model"])


def test_poll_queue_dispatches_step_skipped():
    w = _make_wizard_no_tk()
    w._queue.put(("step_skipped", "model"))
    w._queue.put(("all_done", {}))
    w._poll_queue()
    w._install_frame.step_skipped.assert_called_with("model")


def test_poll_queue_dispatches_step_progress():
    w = _make_wizard_no_tk()
    w._queue.put(("step_progress", "ollama", 0.75))
    w._queue.put(("all_done", {}))
    w._poll_queue()
    w._install_frame.step_progress.assert_called_with("ollama", 0.75)


def test_apply_check_results_computes_steps():
    w = _make_wizard_no_tk()
    mock_frame = MagicMock()
    mock_frame.update_status.return_value = False
    w._apply_check_results(mock_frame, {"ollama": True, "model": False, "vibevoice": False})
    assert set(w._steps_to_install) == {"model", "vibevoice"}


def test_apply_check_results_no_steps_when_all_installed():
    w = _make_wizard_no_tk()
    mock_frame = MagicMock()
    mock_frame.update_status.return_value = True
    w._apply_check_results(mock_frame, {"ollama": True, "model": True, "vibevoice": True})
    assert w._steps_to_install == []
