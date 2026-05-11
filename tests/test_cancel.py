import bertytype.__main__ as app


def test_on_cancel_sets_cancel_event():
    app._cancel_event.clear()
    app._on_cancel()
    assert app._cancel_event.is_set()


def test_on_cancel_sets_stop_event():
    app._stop_event.clear()
    app._on_cancel()
    assert app._stop_event.is_set()
