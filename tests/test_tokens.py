def test_build_qss_returns_nonempty_string():
    from bertytype.ui.tokens import build_qss
    result = build_qss()
    assert isinstance(result, str)
    assert len(result) > 100


def test_build_qss_contains_bg_token():
    from bertytype.ui.tokens import build_qss, BG
    assert BG in build_qss()


def test_build_qss_contains_accent_token():
    from bertytype.ui.tokens import build_qss, ACCENT
    assert ACCENT in build_qss()


def test_build_qss_contains_border_token():
    from bertytype.ui.tokens import build_qss, BORDER
    assert BORDER in build_qss()


def test_build_qss_contains_text_token():
    from bertytype.ui.tokens import build_qss, TEXT
    assert TEXT in build_qss()
