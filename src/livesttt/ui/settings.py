from __future__ import annotations
import tkinter as tk
import tkinter.messagebox
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
    if state & 0x20000:
        parts.append("alt")
    parts.append(keysym.lower())
    return "+".join(parts)


class _HotkeyCapture(tk.Frame):
    def __init__(self, parent: tk.Misc, value: str) -> None:
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
        result = build_hotkey_string(int(event.state), event.keysym)
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

    row = 0

    tk.Label(win, text="Mode:").grid(row=row, column=0, padx=8, pady=4, sticky="w")
    mode_var = tk.StringVar(value=cfg.hotkey_mode)
    tk.OptionMenu(win, mode_var, "double_tap_toggle", "ptt").grid(row=row, column=1, padx=8, sticky="w")
    row += 1

    tk.Label(win, text="Hotkey:").grid(row=row, column=0, padx=8, pady=4, sticky="w")
    hotkey_capture = _HotkeyCapture(win, value=cfg.hotkey)
    hotkey_capture.grid(row=row, column=1, padx=8)
    row += 1

    tk.Label(win, text="Double-tap window (s):").grid(row=row, column=0, padx=8, pady=4, sticky="w")
    double_tap_window_var = tk.DoubleVar(value=cfg.double_tap_window)
    tk.Scale(win, from_=0.05, to=2.0, resolution=0.05, variable=double_tap_window_var,
             orient="horizontal", length=150).grid(row=row, column=1, padx=8, sticky="w")
    row += 1

    tk.Label(win, text="Cancel:").grid(row=row, column=0, padx=8, pady=4, sticky="w")
    cancel_capture = _HotkeyCapture(win, value=cfg.cancel_hotkey)
    cancel_capture.grid(row=row, column=1, padx=8)
    row += 1

    tk.Label(win, text="LLM Model:").grid(row=row, column=0, padx=8, pady=4, sticky="w")
    model_var = tk.StringVar(value=cfg.model)
    tk.Entry(win, textvariable=model_var, width=24).grid(row=row, column=1, padx=8)
    row += 1

    refine_var = tk.BooleanVar(value=cfg.refine)
    tk.Checkbutton(win, text="Refine with LLM", variable=refine_var).grid(
        row=row, column=0, columnspan=2, padx=8, pady=4, sticky="w"
    )
    row += 1

    tk.Label(win, text="VAD Threshold:").grid(row=row, column=0, padx=8, pady=4, sticky="w")
    vad_var = tk.DoubleVar(value=cfg.vad_threshold)
    tk.Scale(win, from_=0.0, to=0.5, resolution=0.01, variable=vad_var,
             orient="horizontal", length=150).grid(row=row, column=1, padx=8, sticky="w")
    row += 1

    tk.Label(win, text="LLM Timeout (s):").grid(row=row, column=0, padx=8, pady=4, sticky="w")
    llm_timeout_var = tk.IntVar(value=cfg.llm_timeout)
    tk.Entry(win, textvariable=llm_timeout_var, width=8).grid(row=row, column=1, padx=8, sticky="w")
    row += 1

    tk.Label(win, text="Injection Delay (s):").grid(row=row, column=0, padx=8, pady=4, sticky="w")
    injection_delay_var = tk.DoubleVar(value=cfg.injection_delay)
    tk.Entry(win, textvariable=injection_delay_var, width=8).grid(row=row, column=1, padx=8, sticky="w")
    row += 1

    def _save() -> None:
        try:
            updated = Config(
                hotkey=hotkey_capture.get(),
                cancel_hotkey=cancel_capture.get(),
                model=model_var.get().strip(),
                refine=refine_var.get(),
                vad_threshold=vad_var.get(),
                hotkey_mode=mode_var.get(),
                double_tap_window=double_tap_window_var.get(),
                llm_timeout=llm_timeout_var.get(),
                injection_delay=injection_delay_var.get(),
            )
        except tk.TclError as e:
            tk.messagebox.showerror("Invalid input", f"Please correct the highlighted fields.\n\n{e}")
            return
        on_save(updated)
        win.destroy()

    tk.Button(win, text="Save", command=_save).grid(
        row=row, column=0, columnspan=2, pady=8
    )
    win.mainloop()
