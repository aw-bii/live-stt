import pytest

from bertytype.ui.settings import build_hotkey_string


def test_returns_none_for_control_l():
    assert build_hotkey_string(0, "Control_L") is None


def test_returns_none_for_shift_r():
    assert build_hotkey_string(0, "Shift_R") is None


def test_returns_none_for_alt_l():
    assert build_hotkey_string(0, "Alt_L") is None


def test_plain_key_no_modifiers():
    assert build_hotkey_string(0, "space") == "space"


def test_ctrl_modifier():
    assert build_hotkey_string(0x4, "space") == "ctrl+space"


def test_ctrl_shift_modifier():
    assert build_hotkey_string(0x4 | 0x1, "space") == "ctrl+shift+space"


def test_alt_modifier():
    assert build_hotkey_string(0x20000, "f9") == "alt+f9"


def test_mod1_bit_not_treated_as_alt():
    # 0x8 is NumLock/Mod1 on Windows, not Alt - should produce no modifier prefix
    assert build_hotkey_string(0x8, "f9") == "f9"


def test_keysym_is_lowercased():
    assert build_hotkey_string(0, "Return") == "return"


@pytest.fixture(scope="module")
def ctk_root():
    try:
        import customtkinter as ctk
        ctk.set_appearance_mode("dark")
        root = ctk.CTk()
        root.withdraw()
        yield root
        root.destroy()
    except Exception:
        pytest.skip("No display available")


def test_capture_initial_value(ctk_root):
    from bertytype.ui.settings import _HotkeyCapture
    cap = _HotkeyCapture(ctk_root, "ctrl+alt+space")
    assert cap.get() == "ctrl+alt+space"


def test_capture_key_updates_value(ctk_root):
    from bertytype.ui.settings import _HotkeyCapture

    class _Ev:
        state = 0x4  # ctrl bit
        keysym = "f9"

    cap = _HotkeyCapture(ctk_root, "alt")
    cap._active = True
    cap._on_key(_Ev())
    assert cap.get() == "ctrl+f9"


def test_capture_focus_out_restores_previous(ctk_root):
    from bertytype.ui.settings import _HotkeyCapture
    cap = _HotkeyCapture(ctk_root, "escape")
    cap._active = True
    cap._prev = "escape"
    cap._on_focus_out()
    assert cap.get() == "escape"


def test_capture_ignores_lone_modifier(ctk_root):
    from bertytype.ui.settings import _HotkeyCapture

    class _Ev:
        state = 0x4
        keysym = "Control_L"

    cap = _HotkeyCapture(ctk_root, "alt")
    cap._active = True
    cap._on_key(_Ev())
    assert cap._active is True
    assert cap.get() == "alt"
