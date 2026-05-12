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
            lbl = ctk.CTkLabel(
                self._inner, text=value or "Press hotkey...",
                font=_FONT_SM, text_color=_HINT,
            )
            lbl.pack(side="left")
            lbl.bind("<Button-1>", self._start_capture)
            return
        for i, part in enumerate(value.split("+")):
            if i:
                sep = ctk.CTkLabel(
                    self._inner, text="+", font=_FONT_SM, text_color=_HINT,
                )
                sep.pack(side="left", padx=2)
                sep.bind("<Button-1>", self._start_capture)
            badge = ctk.CTkFrame(
                self._inner, fg_color="#1a1a1a",
                border_color=_BORDER, border_width=1, corner_radius=4,
            )
            badge.pack(side="left", padx=1)
            badge.bind("<Button-1>", self._start_capture)
            lbl = ctk.CTkLabel(
                badge, text=part, font=_FONT_SM, text_color=_TEXT_DIM,
            )
            lbl.pack(padx=5, pady=2)
            lbl.bind("<Button-1>", self._start_capture)

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


def open_settings(cfg: Config, on_save: Callable[[Config], None]) -> None:
    ctk.set_appearance_mode("dark")

    win = ctk.CTk()
    win.title("BertyType Settings")
    win.geometry("540x560")
    win.resizable(False, False)
    win.configure(fg_color=_BG)

    content = ctk.CTkFrame(win, fg_color=_BG, corner_radius=0)
    content.pack(fill="both", expand=True)

    def _sep() -> None:
        sep = tk.Frame(content, height=1, bg=_BORDER)
        sep.pack(fill="x")
        sep.pack_propagate(False)

    def _row(label: str, hint: str) -> ctk.CTkFrame:
        row = ctk.CTkFrame(content, fg_color="transparent", corner_radius=0)
        row.pack(fill="x")
        lft = ctk.CTkFrame(row, fg_color="transparent")
        lft.pack(side="left", fill="both", expand=True, padx=17, pady=9)
        ctk.CTkLabel(lft, text=label, font=_FONT,    text_color=_TEXT, anchor="w").pack(fill="x")
        ctk.CTkLabel(lft, text=hint,  font=_FONT_SM, text_color=_HINT, anchor="w").pack(fill="x")
        rgt = ctk.CTkFrame(row, fg_color="transparent")
        rgt.pack(side="right", padx=17, pady=9)
        return rgt

    # Row 1 - Recording Mode
    mode_var = tk.StringVar(value=cfg.hotkey_mode)
    ctk.CTkOptionMenu(
        _row("Recording Mode", "How to start and stop recording"),
        variable=mode_var, values=["ptt", "double_tap_toggle"],
        fg_color=_BG_ELEVATED, button_color=_BORDER, button_hover_color="#333333",
        text_color=_TEXT, dropdown_fg_color="#161616",
        dropdown_hover_color="#272727", dropdown_text_color=_TEXT,
        font=_FONT, dropdown_font=_FONT, width=160, corner_radius=6,
    ).pack()
    _sep()

    # Row 2 - Hotkey
    hotkey_cap = _HotkeyCapture(
        _row("Hotkey", "Key to hold (PTT) or tap (toggle)"), cfg.hotkey
    )
    hotkey_cap.pack()
    _sep()

    # Row 3 - Double-tap Window
    dbl_var = tk.DoubleVar(value=cfg.double_tap_window)
    dbl_ctrl = ctk.CTkFrame(
        _row("Double-tap Window", "Max gap between taps (0.05 - 2.0 s)"),
        fg_color="transparent",
    )
    dbl_ctrl.pack()
    dbl_lbl = ctk.CTkLabel(
        dbl_ctrl, text=f"{cfg.double_tap_window:.2f}s",
        font=_FONT, text_color=_GREEN, width=42, anchor="e",
    )
    dbl_lbl.pack(side="right", padx=(6, 0))

    def _on_dbl(v: float) -> None:
        snapped = round(round(v / 0.05) * 0.05, 2)
        dbl_var.set(snapped)
        dbl_lbl.configure(text=f"{snapped:.2f}s")

    ctk.CTkSlider(
        dbl_ctrl, from_=0.05, to=2.0, variable=dbl_var, command=_on_dbl,
        width=110, fg_color=_BG_ELEVATED, progress_color=_GREEN,
        button_color=_GREEN, button_hover_color=_GREEN_HVR,
    ).pack(side="left")
    _sep()

    # Row 4 - Cancel Hotkey
    cancel_cap = _HotkeyCapture(
        _row("Cancel Hotkey", "Abort an in-progress recording"), cfg.cancel_hotkey
    )
    cancel_cap.pack()
    _sep()

    # Row 5 - LLM Model
    model_var = tk.StringVar(value=cfg.model)
    ctk.CTkEntry(
        _row("LLM Model", "Ollama model name for refinement"),
        textvariable=model_var, width=140, font=_FONT,
        fg_color=_BG_ELEVATED, border_color=_BORDER, text_color=_TEXT, corner_radius=6,
    ).pack()
    _sep()

    # Row 6 - Refine with LLM
    refine_var = tk.BooleanVar(value=cfg.refine)
    ctk.CTkSwitch(
        _row("Refine with LLM", "Pass STT output through Gemma 4"),
        variable=refine_var, text="",
        fg_color="#333333", progress_color=_GREEN,
        button_color="#ffffff", button_hover_color="#dddddd",
    ).pack()
    _sep()

    # Row 7 - VAD Threshold
    vad_var = tk.DoubleVar(value=cfg.vad_threshold)
    vad_ctrl = ctk.CTkFrame(
        _row("VAD Threshold", "Voice activity sensitivity (0.0 - 0.5)"),
        fg_color="transparent",
    )
    vad_ctrl.pack()
    vad_lbl = ctk.CTkLabel(
        vad_ctrl, text=f"{cfg.vad_threshold:.2f}",
        font=_FONT, text_color=_GREEN, width=36, anchor="e",
    )
    vad_lbl.pack(side="right", padx=(6, 0))

    def _on_vad(v: float) -> None:
        snapped = round(round(v / 0.01) * 0.01, 2)
        vad_var.set(snapped)
        vad_lbl.configure(text=f"{snapped:.2f}")

    ctk.CTkSlider(
        vad_ctrl, from_=0.0, to=0.5, variable=vad_var, command=_on_vad,
        width=110, fg_color=_BG_ELEVATED, progress_color=_GREEN,
        button_color=_GREEN, button_hover_color=_GREEN_HVR,
    ).pack(side="left")
    _sep()

    # Row 8 - LLM Timeout
    llm_to_var = tk.StringVar(value=str(cfg.llm_timeout))
    to_ctrl = ctk.CTkFrame(
        _row("LLM Timeout", "Seconds before giving up on LLM"),
        fg_color="transparent",
    )
    to_ctrl.pack()
    ctk.CTkEntry(
        to_ctrl, textvariable=llm_to_var, width=58, font=_FONT,
        fg_color=_BG_ELEVATED, border_color=_BORDER, text_color=_TEXT, corner_radius=6,
    ).pack(side="left")
    ctk.CTkLabel(to_ctrl, text="sec", font=_FONT_SM, text_color=_HINT).pack(
        side="left", padx=(5, 0)
    )
    _sep()

    # Row 9 - Injection Delay  (no separator after last row)
    inj_var = tk.StringVar(value=str(cfg.injection_delay))
    inj_ctrl = ctk.CTkFrame(
        _row("Injection Delay", "Pause before typing into active window"),
        fg_color="transparent",
    )
    inj_ctrl.pack()
    ctk.CTkEntry(
        inj_ctrl, textvariable=inj_var, width=58, font=_FONT,
        fg_color=_BG_ELEVATED, border_color=_BORDER, text_color=_TEXT, corner_radius=6,
    ).pack(side="left")
    ctk.CTkLabel(inj_ctrl, text="sec", font=_FONT_SM, text_color=_HINT).pack(
        side="left", padx=(5, 0)
    )

    # Error label (hidden until a save attempt fails)
    error_lbl = ctk.CTkLabel(win, text="", font=_FONT_SM, text_color=_RED, anchor="e")
    error_lbl.pack(fill="x", padx=17, pady=(6, 0))

    # Footer
    tk.Frame(win, height=1, bg=_BORDER).pack(fill="x")
    footer = ctk.CTkFrame(win, fg_color=_BG, corner_radius=0)
    footer.pack(fill="x", padx=17, pady=11)

    def _save() -> None:
        error_lbl.configure(text="")
        try:
            llm_to  = int(llm_to_var.get())
            inj_del = float(inj_var.get())
        except ValueError as exc:
            error_lbl.configure(text=f"Invalid value: {exc}")
            return
        on_save(Config(
            hotkey=hotkey_cap.get(),
            cancel_hotkey=cancel_cap.get(),
            model=model_var.get().strip(),
            refine=bool(refine_var.get()),
            vad_threshold=round(vad_var.get(), 3),
            hotkey_mode=mode_var.get(),
            double_tap_window=round(dbl_var.get(), 3),
            llm_timeout=llm_to,
            injection_delay=inj_del,
        ))
        win.destroy()

    ctk.CTkButton(
        footer, text="Save Settings", command=_save,
        fg_color=_GREEN, hover_color=_GREEN_HVR, text_color="#000000",
        font=_FONT, corner_radius=100, width=130, height=32,
    ).pack(side="right")

    win.mainloop()
