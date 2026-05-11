from __future__ import annotations
import tkinter as tk
import customtkinter as ctk
from typing import Callable
from bertytype.config import Config

_BG          = "#0f0f0f"
_BG_ELEVATED = "#1e1e1e"
_BORDER      = "#272727"
_GREEN       = "#1ed760"
_GREEN_HVR   = "#22e865"
_TEXT        = "#f0f0f0"
_HINT        = "#444444"
_TEXT_DIM    = "#888888"
_RED         = "#e84040"
_FONT        = ("Consolas", 11)
_FONT_SM     = ("Consolas", 9)

_MODIFIER_KEYSYMS = frozenset({
    "Control_L", "Control_R", "Shift_L", "Shift_R",
    "Alt_L", "Alt_R", "Meta_L", "Meta_R",
})


def build_hotkey_string(state: int, keysym: str) -> str | None:
    if keysym in _MODIFIER_KEYSYMS:
        return None
    parts = []
    if state & 0x4:
        parts.append("ctrl")
    if state & 0x1:
        parts.append("shift")
    if state & 0x20000:
        parts.append("alt")
    parts.append(keysym.lower())
    return "+".join(parts)


class _HotkeyCapture(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkBaseClass, value: str) -> None:
        super().__init__(
            parent,
            fg_color=_BG_ELEVATED, border_color=_BORDER,
            border_width=1, corner_radius=6, cursor="hand2",
        )
        self._prev   = value
        self._value  = value
        self._active = False
        self._inner  = ctk.CTkFrame(self, fg_color="transparent")
        self._inner.pack(padx=9, pady=5)
        self._render(value)
        self.bind("<Button-1>", self._start_capture)
        self._inner.bind("<Button-1>", self._start_capture)
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<KeyPress>", self._on_key)
        tk.Widget.configure(self, takefocus=True)

    def _render(self, value: str) -> None:
        for w in self._inner.winfo_children():
            w.destroy()
        if not value or value == "Press hotkey...":
            ctk.CTkLabel(
                self._inner, text=value or "Press hotkey...",
                font=_FONT_SM, text_color=_HINT,
            ).pack(side="left")
            return
        for i, part in enumerate(value.split("+")):
            if i:
                ctk.CTkLabel(
                    self._inner, text="+", font=_FONT_SM, text_color=_HINT,
                ).pack(side="left", padx=2)
            badge = ctk.CTkFrame(
                self._inner, fg_color="#1a1a1a",
                border_color=_BORDER, border_width=1, corner_radius=4,
            )
            badge.pack(side="left", padx=1)
            ctk.CTkLabel(
                badge, text=part, font=_FONT_SM, text_color=_TEXT_DIM,
            ).pack(padx=5, pady=2)

    def _start_capture(self, _event=None) -> None:
        self._prev   = self._value
        self._active = True
        self.configure(border_color=_GREEN)
        self._render("Press hotkey...")
        self.focus_set()

    def _on_focus_out(self, _event=None) -> None:
        if self._active:
            self._active = False
            self.configure(border_color=_BORDER)
            self._value = self._prev
            self._render(self._prev)

    def _on_key(self, event) -> str:
        if not self._active:
            return ""
        result = build_hotkey_string(int(event.state), event.keysym)
        if result is not None:
            self._active = False
            self.configure(border_color=_BORDER)
            self._value  = result
            self._render(result)
        return "break"

    def get(self) -> str:
        return self._value
