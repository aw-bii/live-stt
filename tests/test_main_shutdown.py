import threading
from unittest.mock import patch
from livesttt import __main__ as app


def test_health_monitor_stops_when_quit_event_is_set():
    app._quit_event.clear()

    with patch.object(app, "_check_health", return_value={"vibevoice": False, "ollama": False}):
        thread = threading.Thread(
            target=app._periodic_health_check,
            args=(0,),
            daemon=True,
        )
        thread.start()
        app._quit_event.set()
        thread.join(timeout=2.0)

    assert not thread.is_alive(), "Health monitor did not stop after _quit_event was set"
