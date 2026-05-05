from __future__ import annotations
import tkinter as tk
from typing import Callable
from livesttt.config import Config

_MODIFIER_KEYSYMS = frozenset({
    "Control_L", "Control_R",
    "Shift_L", "Shift_R",
    "Alt_L", "Alt_R",
    "Meta_L", "Meta_R",
})


def build_hotkey_string(state: int, keysym: str) -> str | None:
    if keysym in _MODIFIER_KEYSYMS:
        return None
    parts = []
    if state & 0x4:
        parts.append("ctrl")
    if state & 0x1:
        parts.append("shift")
    if state & 0x8:
        parts.append("alt")
    parts.append(keysym.lower())
    return "+".join(parts)


class _HotkeyCapture(tk.Frame):
    def __init__(self, parent: tk.Widget, value: str) -> None:
        super().__init__(parent)
        self._prev = value
        self._var = tk.StringVar(value=value)
        entry = tk.Entry(self, textvariable=self._var, width=24)
        entry.pack()
        entry.bind("<FocusIn>", self._on_focus_in)
        entry.bind("<FocusOut>", self._on_focus_out)
        entry.bind("<KeyPress>", self._on_key)

    def _on_focus_in(self, _: tk.Event) -> None:
        self._prev = self._var.get()
        self._var.set("Press hotkey...")

    def _on_focus_out(self, _: tk.Event) -> None:
        if self._var.get() == "Press hotkey...":
            self._var.set(self._prev)

    def _on_key(self, event: tk.Event) -> str:
        result = build_hotkey_string(event.state, event.keysym)
        if result is not None:
            self._var.set(result)
        return "break"

    def get(self) -> str:
        v = self._var.get()
        return self._prev if v == "Press hotkey..." else v


def open_settings(cfg: Config, on_save: Callable[[Config], None]) -> None:
    win = tk.Tk()
    win.title("live-stt settings")
    win.resizable(False, False)

    tk.Label(win, text="Hotkey:").grid(row=0, column=0, padx=8, pady=4, sticky="w")
    hotkey_capture = _HotkeyCapture(win, value=cfg.hotkey)
    hotkey_capture.grid(row=0, column=1, padx=8)

    tk.Label(win, text="Model:").grid(row=1, column=0, padx=8, pady=4, sticky="w")
    model_var = tk.StringVar(value=cfg.model)
    tk.Entry(win, textvariable=model_var, width=24).grid(row=1, column=1, padx=8)

    refine_var = tk.BooleanVar(value=cfg.refine)
    tk.Checkbutton(win, text="Refine with LLM", variable=refine_var).grid(
        row=2, column=0, columnspan=2, padx=8, pady=4, sticky="w"
    )

    def _save() -> None:
        updated = Config(
            hotkey=hotkey_capture.get(),
            model=model_var.get().strip(),
            refine=refine_var.get(),
            vad_threshold=cfg.vad_threshold,
        )
        on_save(updated)
        win.destroy()

    tk.Button(win, text="Save", command=_save).grid(
        row=3, column=0, columnspan=2, pady=8
    )
    win.mainloop()
