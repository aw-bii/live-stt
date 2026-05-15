"""Shared color and typography tokens for the BertyType UI."""
from __future__ import annotations

# Surfaces
BG          = "#0f0f0f"
BG_ELEVATED = "#1e1e1e"
BG_BADGE    = "#1a1a1a"
BORDER      = "#272727"

# Text
TEXT        = "#f0f0f0"
TEXT_DIM    = "#888888"
HINT        = "#808080"  # minimum contrast: 4.6:1 on BG (#0f0f0f), meets WCAG AA

# Semantic
ACCENT      = "#1ed760"
ACCENT_HVR  = "#22e865"
DESTRUCTIVE = "#e84040"
WARNING     = "#f5a623"

# Tray status icon colors (aligned with semantic tokens above)
STATUS_COLORS: dict[str, str] = {
    "idle":       ACCENT,
    "recording":  DESTRUCTIVE,
    "processing": WARNING,
    "error":      TEXT_DIM,
}

# Control-specific surfaces
SWITCH_TRACK   = "#333333"   # CTkSwitch off-state track
SWITCH_BUTTON  = "#ffffff"   # CTkSwitch toggle knob
SWITCH_BTN_HVR = "#dddddd"   # CTkSwitch knob hover
DROPDOWN_BG    = "#161616"   # Option menu dropdown panel

# Typography — Segoe UI is the Windows system UI font; matches the product register
FONT    = ("Segoe UI", 11)
FONT_SM = ("Segoe UI", 9)


def build_qss() -> str:
    return f"""
    QDialog, QWizard {{
        background: {BG};
        color: {TEXT};
    }}
    QLabel {{
        color: {TEXT};
        background: transparent;
    }}
    QLineEdit, QKeySequenceEdit {{
        background: {BG_ELEVATED};
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 4px 8px;
        color: {TEXT};
    }}
    QComboBox {{
        background: {BG_ELEVATED};
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 4px 8px;
        color: {TEXT};
    }}
    QComboBox QAbstractItemView {{
        background: {BG_ELEVATED};
        border: 1px solid {BORDER};
        color: {TEXT};
        selection-background-color: {BG_BADGE};
    }}
    QSlider::groove:horizontal {{
        background: {BG_ELEVATED};
        height: 4px;
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        background: {ACCENT};
        width: 11px;
        height: 11px;
        margin: -4px 0;
        border-radius: 5px;
    }}
    QSlider::sub-page:horizontal {{
        background: {ACCENT};
        border-radius: 2px;
    }}
    QPushButton {{
        background: {BG_ELEVATED};
        border: 1px solid {BORDER};
        border-radius: 100px;
        padding: 6px 18px;
        color: {TEXT};
    }}
    QPushButton:hover {{
        border-color: {ACCENT};
    }}
    QPushButton[accent="true"] {{
        background: {ACCENT};
        border: none;
        color: {BG};
        font-weight: 600;
    }}
    QPushButton[accent="true"]:hover {{
        background: {ACCENT_HVR};
    }}
    QCheckBox::indicator {{
        width: 38px;
        height: 20px;
        border-radius: 10px;
    }}
    QCheckBox::indicator:unchecked {{
        background: {SWITCH_TRACK};
    }}
    QCheckBox::indicator:checked {{
        background: {ACCENT};
    }}
    QScrollArea, QScrollArea > QWidget > QWidget {{
        background: {BG};
        border: none;
    }}
    QScrollBar:vertical {{
        background: {BG};
        width: 8px;
    }}
    QScrollBar::handle:vertical {{
        background: {BORDER};
        border-radius: 4px;
        min-height: 20px;
    }}
    QPlainTextEdit {{
        background: {BG_ELEVATED};
        border: 1px solid {BORDER};
        border-radius: 4px;
        color: {TEXT_DIM};
    }}
    QProgressBar {{
        background: {BG_ELEVATED};
        border: none;
        border-radius: 4px;
        height: 8px;
        text-align: center;
    }}
    QProgressBar::chunk {{
        background: {ACCENT};
        border-radius: 4px;
    }}
    QWizard QPushButton {{
        min-width: 80px;
    }}
    """
