from livesttt.ui.settings import build_hotkey_string


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


def test_ctrl_shift_key_matches_config_default():
    assert build_hotkey_string(0x4 | 0x1, "space") == "ctrl+shift+space"
