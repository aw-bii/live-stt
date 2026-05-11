from __future__ import annotations
import os
import queue
import subprocess
import sys
import threading
from typing import Callable

import tkinter as tk
from tkinter import ttk

from bertytype_setup import checks, installers

TITLE = "BertyType Setup"
WIN_W, WIN_H = 540, 420

DEPS = [
    ("ollama",    "Ollama",              "~90 MB"),
    ("model",     "gemma4:e2b model",    "~2 GB"),
    ("vibevoice", "VibeVoice ASR model", "~1.5 GB"),
    ("ffmpeg",    "ffmpeg",              "Bundled"),
]

_SPINNER = "|/-\\"


class WelcomeFrame(tk.Frame):
    def __init__(self, parent: tk.Widget, on_next: Callable) -> None:
        super().__init__(parent, padx=32, pady=24)
        tk.Label(self, text=TITLE, font=("Segoe UI", 18, "bold")).pack(pady=(0, 8))
        tk.Label(
            self,
            text="This wizard will download and install all required\n"
                 "components for BertyType. An internet connection is required.",
            justify="center",
        ).pack(pady=(0, 16))
        tk.Label(self, text="The following will be installed:", anchor="w").pack(fill="x")
        for _, name, size in DEPS:
            tk.Label(self, text=f"  - {name}  ({size})", anchor="w").pack(fill="x")
        tk.Button(self, text="Next  >", width=14, command=on_next).pack(
            side="bottom", pady=12
        )


class CheckFrame(tk.Frame):
    def __init__(self, parent: tk.Widget, on_install: Callable) -> None:
        super().__init__(parent, padx=32, pady=24)
        tk.Label(self, text="Checking dependencies...", font=("Segoe UI", 13, "bold")).pack(
            pady=(0, 14)
        )
        self._badges: dict[str, tk.Label] = {}
        for key, name, _ in DEPS:
            row = tk.Frame(self)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=name, width=24, anchor="w").pack(side="left")
            badge = tk.Label(row, text="Checking...", width=22, anchor="w", fg="gray")
            badge.pack(side="left")
            self._badges[key] = badge
        self._btn = tk.Button(
            self, text="Install", width=20, command=on_install, state="disabled"
        )
        self._btn.pack(side="bottom", pady=12)

    def update_status(self, status: dict) -> bool:
        """Update badge colours. Returns True if everything is already installed."""
        all_ok = True
        for key, _, _ in DEPS:
            if key == "ffmpeg":
                self._badges[key].config(text="Included", fg="green")
                continue
            if status.get(key, False):
                self._badges[key].config(text="Already installed", fg="green")
            else:
                self._badges[key].config(text="Will be downloaded", fg="darkorange")
                all_ok = False
        if all_ok:
            self._btn.config(text="All done - Launch BertyType", state="normal")
        else:
            self._btn.config(text="Install", state="normal")
        return all_ok


class InstallFrame(tk.Frame):
    def __init__(self, parent: tk.Widget, on_cancel: Callable) -> None:
        super().__init__(parent, padx=32, pady=20)
        tk.Label(self, text="Installing...", font=("Segoe UI", 13, "bold")).pack(
            pady=(0, 10)
        )
        self._indicators: dict[str, tk.Label] = {}
        self._pbars: dict[str, ttk.Progressbar] = {}
        for key, name, _ in DEPS:
            if key == "ffmpeg":
                continue
            row = tk.Frame(self)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=name, width=24, anchor="w").pack(side="left")
            ind = tk.Label(row, text="Pending", width=10, anchor="w", fg="gray")
            ind.pack(side="left")
            pb = ttk.Progressbar(row, length=130, mode="determinate")
            pb.pack(side="left", padx=6)
            self._indicators[key] = ind
            self._pbars[key] = pb

        self._log = tk.Text(
            self, height=7, width=62, font=("Consolas", 8), state="disabled"
        )
        self._log.pack(pady=6)

        self._overall = ttk.Progressbar(self, length=440, mode="determinate")
        self._overall.pack(pady=4)

        self._done = 0
        self._total = 3
        self._spin_idx = 0

        tk.Button(self, text="Cancel", width=10, command=on_cancel).pack(
            side="bottom", pady=6
        )

    def step_start(self, key: str) -> None:
        if key in self._indicators:
            self._indicators[key].config(text="|", fg="royalblue")

    def step_done(self, key: str) -> None:
        if key in self._indicators:
            self._indicators[key].config(text="Done", fg="green")
            self._pbars[key]["value"] = 100
        self._done += 1
        self._overall["value"] = (self._done / self._total) * 100

    def step_failed(self, key: str) -> None:
        if key in self._indicators:
            self._indicators[key].config(text="Failed", fg="red")
        self._done += 1
        self._overall["value"] = (self._done / self._total) * 100

    def step_skipped(self, key: str) -> None:
        if key in self._indicators:
            self._indicators[key].config(text="Skipped", fg="gray")
        self._done += 1
        self._overall["value"] = (self._done / self._total) * 100

    def step_progress(self, key: str, fraction: float) -> None:
        if key in self._pbars:
            self._pbars[key]["value"] = fraction * 100

    def log(self, msg: str) -> None:
        self._log.config(state="normal")
        self._log.insert("end", msg + "\n")
        self._log.see("end")
        self._log.config(state="disabled")

    def tick_spinner(self, key: str) -> None:
        if key in self._indicators:
            c = _SPINNER[self._spin_idx % len(_SPINNER)]
            self._indicators[key].config(text=c)
            self._spin_idx += 1


class FinishFrame(tk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        on_finish: Callable,
        failures: list[str],
    ) -> None:
        super().__init__(parent, padx=32, pady=32)
        if not failures:
            tk.Label(
                self, text="Setup complete!", font=("Segoe UI", 16, "bold"), fg="green"
            ).pack(pady=(0, 16))
            self._launch = tk.BooleanVar(value=True)
            tk.Checkbutton(
                self, text="Launch BertyType now", variable=self._launch
            ).pack(pady=8)
            tk.Button(
                self,
                text="Finish",
                width=14,
                command=lambda: on_finish(self._launch.get()),
            ).pack(pady=12)
        else:
            tk.Label(
                self,
                text="Setup finished with errors",
                font=("Segoe UI", 14, "bold"),
                fg="red",
            ).pack(pady=(0, 10))
            tk.Label(self, text="The following steps failed:", anchor="w").pack(fill="x")
            for name in failures:
                tk.Label(self, text=f"  - {name}", fg="red", anchor="w").pack(fill="x")
            tk.Button(
                self,
                text="Retry failed steps",
                width=20,
                command=lambda: on_finish(False, retry=True),
            ).pack(pady=8)
            tk.Button(
                self, text="Close", width=12, command=lambda: on_finish(False)
            ).pack(pady=4)


class Wizard:
    def __init__(self, root: tk.Tk) -> None:
        self._root = root
        self._root.title(TITLE)
        self._root.geometry(f"{WIN_W}x{WIN_H}")
        self._root.resizable(False, False)
        self._queue: queue.Queue = queue.Queue()
        self._cancel = threading.Event()
        self._current_frame: tk.Frame | None = None
        self._check_results: dict = {}
        self._failures: list[str] = []
        self._steps_to_install: list[str] = []
        self._install_frame: InstallFrame | None = None
        self._show_welcome()

    def _clear(self) -> None:
        if self._current_frame is not None:
            self._current_frame.pack_forget()

    def _show_welcome(self) -> None:
        self._clear()
        self._current_frame = WelcomeFrame(self._root, on_next=self._show_check)
        self._current_frame.pack(fill="both", expand=True)

    def _show_check(self) -> None:
        self._clear()
        frame = CheckFrame(self._root, on_install=self._start_install)
        self._current_frame = frame
        frame.pack(fill="both", expand=True)
        threading.Thread(target=self._run_checks, args=(frame,), daemon=True).start()

    def _run_checks(self, frame: CheckFrame) -> None:
        result = checks.check_all()
        self._root.after(0, lambda: self._apply_check_results(frame, result))

    def _apply_check_results(self, frame: CheckFrame, result: dict) -> None:
        self._check_results = result
        all_ok = frame.update_status(result)
        if all_ok:
            self._steps_to_install = []
        else:
            self._steps_to_install = [
                k for k in ("ollama", "model", "vibevoice")
                if not result.get(k, False)
            ]

    def _start_install(self) -> None:
        if not self._steps_to_install:
            self._show_finish([])
            return
        self._cancel.clear()
        self._failures = []
        self._clear()
        frame = InstallFrame(self._root, on_cancel=self._cancel_install)
        self._install_frame = frame
        self._current_frame = frame
        frame.pack(fill="both", expand=True)
        self._root.after(100, self._poll_queue)
        threading.Thread(
            target=installers.run_all_installs,
            args=(self._queue, self._cancel, self._steps_to_install),
            daemon=True,
        ).start()

    def _poll_queue(self) -> None:
        f = self._install_frame
        try:
            while True:
                item = self._queue.get_nowait()
                event, *args = item
                if event == "log":
                    f.log(args[0])
                elif event == "step_start":
                    f.step_start(args[0])
                elif event == "step_done":
                    f.step_done(args[0])
                elif event == "step_failed":
                    f.step_failed(args[0])
                    self._failures.append(args[0])
                elif event == "step_skipped":
                    f.step_skipped(args[0])
                elif event == "step_progress":
                    f.step_progress(args[0], args[1])
                elif event == "all_done":
                    self._show_finish(self._failures)
                    return
        except queue.Empty:
            pass
        self._root.after(100, self._poll_queue)

    def _cancel_install(self) -> None:
        self._cancel.set()

    def _show_finish(self, failures: list[str]) -> None:
        self._clear()
        frame = FinishFrame(self._root, on_finish=self._finish, failures=failures)
        self._current_frame = frame
        frame.pack(fill="both", expand=True)

    def _finish(self, launch: bool, retry: bool = False) -> None:
        if retry:
            self._steps_to_install = list(self._failures)
            self._failures = []
            self._start_install()
            return
        if launch:
            exe = os.path.join(os.path.dirname(sys.executable), "bertytype.exe")
            if os.path.exists(exe):
                subprocess.Popen([exe])
        self._root.destroy()
