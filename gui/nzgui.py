#!/usr/bin/env python3
"""Super File Compressor - NZ GUI.

Dependency-free Tkinter front-end for the native nzcompress executable.
The GUI intentionally delegates compression/extraction to the tested C++ engine.
"""

from __future__ import annotations

import hashlib
import os
import queue
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

APP_NAME = "Super File Compressor"
VERSION = "NZ v0.2 GUI"


def find_engine() -> str | None:
    here = Path(__file__).resolve()
    candidates = [
        here.parent.parent / "build" / "nzcompress",
        here.parent.parent / "build" / "Release" / "nzcompress",
        Path.cwd() / "build" / "nzcompress",
        Path.cwd() / "nzcompress",
    ]
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return shutil.which("nzcompress")


def sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


class NZGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_NAME} — {VERSION}")
        self.geometry("920x650")
        self.minsize(780, 560)

        self.engine = tk.StringVar(value=find_engine() or "")
        self.mode = tk.StringVar(value="compress")
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.verify = tk.BooleanVar(value=True)
        self.status = tk.StringVar(value="Ready")
        self.progress = tk.DoubleVar(value=0)
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.running = False

        self._style()
        self._build()
        self.after(100, self._poll_events)

    def _style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Title.TLabel", font=("TkDefaultFont", 20, "bold"))
        style.configure("Sub.TLabel", font=("TkDefaultFont", 10))
        style.configure("Run.TButton", font=("TkDefaultFont", 11, "bold"), padding=10)

    def _build(self) -> None:
        root = ttk.Frame(self, padding=18)
        root.pack(fill="both", expand=True)

        header = ttk.Frame(root)
        header.pack(fill="x", pady=(0, 14))
        ttk.Label(header, text="Super File Compressor", style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="Native NZ archive manager • C++ engine + integrity verification", style="Sub.TLabel").pack(anchor="w", pady=(3, 0))

        mode = ttk.LabelFrame(root, text="Operation", padding=12)
        mode.pack(fill="x", pady=(0, 12))
        ttk.Radiobutton(mode, text="Compress → .nz", variable=self.mode, value="compress", command=self._mode_changed).pack(side="left", padx=(0, 20))
        ttk.Radiobutton(mode, text="Extract .nz", variable=self.mode, value="extract", command=self._mode_changed).pack(side="left")

        paths = ttk.LabelFrame(root, text="Files", padding=12)
        paths.pack(fill="x", pady=(0, 12))
        self._path_row(paths, "Input", self.input_path, self._choose_input, 0)
        self._path_row(paths, "Output", self.output_path, self._choose_output, 1)

        options = ttk.LabelFrame(root, text="Options", padding=12)
        options.pack(fill="x", pady=(0, 12))
        ttk.Checkbutton(options, text="Verify output after operation", variable=self.verify).pack(side="left")
        ttk.Label(options, text="Current engine: 64 MiB streaming chunks • Zstandard • XXH64").pack(side="right")

        actions = ttk.Frame(root)
        actions.pack(fill="x", pady=(0, 12))
        self.run_button = ttk.Button(actions, text="Start Compression", style="Run.TButton", command=self.start)
        self.run_button.pack(side="left")
        self.clear_button = ttk.Button(actions, text="Clear", command=self.clear)
        self.clear_button.pack(side="left", padx=8)
        self.open_button = ttk.Button(actions, text="Open Output Folder", command=self.open_output_folder)
        self.open_button.pack(side="left")
        ttk.Label(actions, textvariable=self.status).pack(side="right")

        log_frame = ttk.LabelFrame(root, text="Operation Log", padding=8)
        log_frame.pack(fill="both", expand=True)
        self.log = tk.Text(log_frame, height=12, wrap="word", state="disabled", font=("TkFixedFont", 10))
        scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.progress_bar = ttk.Progressbar(root, variable=self.progress, maximum=100, mode="indeterminate")
        self.progress_bar.pack(fill="x", pady=(10, 0))

        self._log("Ready. Select an input file and choose Compress or Extract.")
        if not self.engine.get():
            self._log("WARNING: nzcompress was not found. Build the project first with CMake.")

    def _path_row(self, parent: ttk.Widget, label: str, variable: tk.StringVar, command, row: int) -> None:
        ttk.Label(parent, text=label, width=10).grid(row=row, column=0, sticky="w", pady=6)
        entry = ttk.Entry(parent, textvariable=variable)
        entry.grid(row=row, column=1, sticky="ew", padx=8, pady=6)
        ttk.Button(parent, text="Browse…", command=command).grid(row=row, column=2, pady=6)
        parent.columnconfigure(1, weight=1)

    def _mode_changed(self) -> None:
        if self.mode.get() == "compress":
            self.run_button.configure(text="Start Compression")
            if self.input_path.get() and not self.output_path.get():
                self._auto_output()
        else:
            self.run_button.configure(text="Start Extraction")
            if self.input_path.get() and not self.output_path.get():
                self._auto_output()

    def _choose_input(self) -> None:
        if self.mode.get() == "compress":
            path = filedialog.askopenfilename(title="Choose file to compress")
        else:
            path = filedialog.askopenfilename(title="Choose NZ archive", filetypes=[("NZ archives", "*.nz"), ("All files", "*")])
        if path:
            self.input_path.set(path)
            self._auto_output()

    def _choose_output(self) -> None:
        if self.mode.get() == "compress":
            initial = Path(self.input_path.get()).stem + ".nz" if self.input_path.get() else "archive.nz"
            path = filedialog.asksaveasfilename(title="Save NZ archive", defaultextension=".nz", initialfile=initial, filetypes=[("NZ archives", "*.nz"), ("All files", "*")])
        else:
            initial = Path(self.input_path.get()).stem if self.input_path.get() else "restored-file"
            path = filedialog.asksaveasfilename(title="Save extracted file", initialfile=initial)
        if path:
            self.output_path.set(path)

    def _auto_output(self) -> None:
        source = Path(self.input_path.get())
        if not source.exists():
            return
        if self.mode.get() == "compress":
            self.output_path.set(str(source.with_suffix(source.suffix + ".nz") if source.suffix else source.with_name(source.name + ".nz")))
        else:
            name = source.name[:-3] if source.name.lower().endswith(".nz") else source.stem + "-restored"
            self.output_path.set(str(source.with_name(name)))

    def clear(self) -> None:
        if self.running:
            return
        self.input_path.set("")
        self.output_path.set("")
        self.progress.set(0)
        self.status.set("Ready")
        self._log("Cleared.")

    def open_output_folder(self) -> None:
        path = self.output_path.get()
        folder = str(Path(path).parent if path else Path.cwd())
        try:
            if sys.platform.startswith("linux"):
                subprocess.Popen(["xdg-open", folder])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                os.startfile(folder)  # type: ignore[attr-defined]
        except Exception as exc:
            messagebox.showerror("Open folder", str(exc))

    def start(self) -> None:
        if self.running:
            return
        engine = self.engine.get().strip()
        source = self.input_path.get().strip()
        destination = self.output_path.get().strip()
        if not engine or not Path(engine).is_file():
            messagebox.showerror("NZ engine not found", "Build the project first, then start the GUI again.\n\nExpected: build/nzcompress")
            return
        if not source or not Path(source).is_file():
            messagebox.showerror("Input required", "Choose an existing input file.")
            return
        if not destination:
            self._auto_output()
            destination = self.output_path.get().strip()
        if not destination:
            messagebox.showerror("Output required", "Choose an output path.")
            return
        if Path(source).resolve() == Path(destination).resolve():
            messagebox.showerror("Invalid output", "Input and output must be different files.")
            return
        if Path(destination).exists():
            if not messagebox.askyesno("Overwrite", f"Overwrite existing file?\n\n{destination}"):
                return

        self.running = True
        self.run_button.configure(state="disabled")
        self.clear_button.configure(state="disabled")
        self.status.set("Working…")
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start(12)
        threading.Thread(target=self._worker, args=(engine, source, destination), daemon=True).start()

    def _worker(self, engine: str, source: str, destination: str) -> None:
        command = [engine, self.mode.get(), source, destination]
        try:
            self.events.put(("log", "$ " + " ".join(self._quote(x) for x in command)))
            process = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            output = process.stdout.strip()
            if output:
                self.events.put(("log", output))
            if process.returncode != 0:
                raise RuntimeError(f"NZ engine exited with code {process.returncode}")

            if self.verify.get():
                if self.mode.get() == "extract":
                    self.events.put(("log", "SHA-256: " + sha256(destination)))
                else:
                    self.events.put(("log", f"Archive created: {os.path.getsize(destination):,} bytes"))

            self.events.put(("done", destination))
        except Exception as exc:
            self.events.put(("error", str(exc)))

    @staticmethod
    def _quote(value: str) -> str:
        return '"' + value.replace('"', '\\"') + '"' if any(c.isspace() for c in value) else value

    def _poll_events(self) -> None:
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "log":
                    self._log(str(value))
                elif kind == "done":
                    self._finish(True, str(value))
                elif kind == "error":
                    self._finish(False, str(value))
        except queue.Empty:
            pass
        self.after(100, self._poll_events)

    def _finish(self, success: bool, detail: str) -> None:
        self.running = False
        self.run_button.configure(state="normal")
        self.clear_button.configure(state="normal")
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate")
        self.progress.set(100 if success else 0)
        if success:
            self.status.set("Completed")
            self._log("Operation completed successfully.")
            messagebox.showinfo("NZ operation complete", f"Successfully completed.\n\nOutput:\n{detail}")
        else:
            self.status.set("Failed")
            self._log("ERROR: " + detail)
            messagebox.showerror("NZ operation failed", detail)

    def _log(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")


if __name__ == "__main__":
    app = NZGui()
    app.mainloop()
