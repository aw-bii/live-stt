import queue
import threading
from unittest.mock import patch


def test_check_worker_emits_check_done(qapp):
    from bertytype_setup.wizard import _CheckWorker
    from PySide6.QtTest import QSignalSpy

    fake_result = {"ollama": True, "model": False, "vibevoice": False}
    with patch("bertytype_setup.checks.check_all", return_value=fake_result):
        worker = _CheckWorker()
        spy = QSignalSpy(worker.check_done)
        worker.run()
        assert spy.count() == 1
        assert spy.at(0)[0] == fake_result


def test_install_worker_emits_log(qapp):
    from bertytype_setup.wizard import _InstallWorker
    from PySide6.QtTest import QSignalSpy

    cancel = threading.Event()

    def fake_install(q, cancel, steps):
        q.put(("log", "hello world"))
        q.put(("all_done",))

    with patch("bertytype_setup.installers.run_all_installs", fake_install):
        worker = _InstallWorker(["ollama"], cancel)
        spy = QSignalSpy(worker.log_msg)
        worker.run()
        assert spy.count() == 1
        assert spy.at(0)[0] == "hello world"


def test_install_worker_records_failures(qapp):
    from bertytype_setup.wizard import _InstallWorker
    from PySide6.QtTest import QSignalSpy

    cancel = threading.Event()

    def fake_install(q, cancel, steps):
        q.put(("step_failed", "model"))
        q.put(("all_done",))

    with patch("bertytype_setup.installers.run_all_installs", fake_install):
        worker = _InstallWorker(["model"], cancel)
        spy = QSignalSpy(worker.all_done)
        worker.run()
        assert spy.count() == 1
        assert spy.at(0)[0] == ["model"]


def test_install_worker_emits_step_progress(qapp):
    from bertytype_setup.wizard import _InstallWorker
    from PySide6.QtTest import QSignalSpy

    cancel = threading.Event()

    def fake_install(q, cancel, steps):
        q.put(("step_progress", "ollama", 0.5))
        q.put(("all_done",))

    with patch("bertytype_setup.installers.run_all_installs", fake_install):
        worker = _InstallWorker(["ollama"], cancel)
        spy = QSignalSpy(worker.step_progress)
        worker.run()
        assert spy.count() == 1
        assert spy.at(0)[0] == "ollama"
        assert abs(spy.at(0)[1] - 0.5) < 0.001


def test_check_page_steps_to_install_computes_missing(qapp):
    from bertytype_setup.wizard import CheckPage
    page = CheckPage()
    page._on_check_done({"ollama": True, "model": False, "vibevoice": False})
    assert set(page.steps_to_install()) == {"model", "vibevoice"}


def test_check_page_no_steps_when_all_present(qapp):
    from bertytype_setup.wizard import CheckPage
    page = CheckPage()
    page._on_check_done({"ollama": True, "model": True, "vibevoice": True})
    assert page.steps_to_install() == []
