from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Callable
from livesttt.config import Config


def open_settings(cfg: Config, on_save: Callable[[Config], None]) -> None:
    win = tk.Tk()
    win.title("live-stt settings")
    win.resizable(False, False)

    tk.Label(win, text="Hotkey:").grid(row=0, column=0, padx=8, pady=4, sticky="w")
    hotkey_var = tk.StringVar(value=cfg.hotkey)
    tk.Entry(win, textvariable=hotkey_var, width=24).grid(row=0, column=1, padx=8)

    tk.Label(win, text="Model:").grid(row=1, column=0, padx=8, pady=4, sticky="w")
    model_var = tk.StringVar(value=cfg.model)
    tk.Entry(win, textvariable=model_var, width=24).grid(row=1, column=1, padx=8)

    refine_var = tk.BooleanVar(value=cfg.refine)
    tk.Checkbutton(win, text="Refine with LLM", variable=refine_var).grid(
        row=2, column=0, columnspan=2, padx=8, pady=4, sticky="w"
    )

    def _save():
        updated = Config(
            hotkey=hotkey_var.get().strip(),
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
