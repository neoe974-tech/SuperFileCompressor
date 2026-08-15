#!/usr/bin/env python3
"""Super File Compressor NZ v3 desktop application."""
from __future__ import annotations
import hashlib
import hmac
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
VERSION = "NZ v3.0.0"
KEY_CONTEXT = b"NZ-V3-UNIVERSAL-PASSWORD-KEY"


def find_engine() -> str | None:
    here = Path(__file__).resolve()
    roots = [here.parent.parent / "build", here.parent.parent / "build" / "Release", here.parent]
    if getattr(sys, "frozen", False):
        roots.insert(0, Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)))
        roots.insert(0, Path(sys.executable).parent)
    for root in roots:
        for name in ("nzcompress.exe", "nzcompress"):
            candidate = root / name
            if candidate.is_file():
                return str(candidate)
    return shutil.which("nzcompress")


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def universal_key(password: str) -> bytes:
    return hmac.new(KEY_CONTEXT, password.encode("utf-8"), hashlib.sha256).digest()


class NZGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_NAME} — {VERSION}")
        self.geometry("1050x760")
        self.minsize(900, 650)
        self.engine = tk.StringVar(value=find_engine() or "")
        self.mode = tk.StringVar(value="compress")
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.password = tk.StringVar()
        self.confirm_password = tk.StringVar()
        self.key_fingerprint = tk.StringVar(value="No password key generated")
        self.verify = tk.BooleanVar(value=True)
        self.status = tk.StringVar(value="Ready")
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.running = False
        self._build_style(); self._build_menu(); self._build_toolbar(); self._build_ui()
        self.after(100, self._poll_events)

    def _build_style(self) -> None:
        style = ttk.Style(self)
        try: style.theme_use("clam")
        except tk.TclError: pass
        style.configure("Title.TLabel", font=("TkDefaultFont", 21, "bold"))
        style.configure("Sub.TLabel", font=("TkDefaultFont", 10))
        style.configure("Run.TButton", font=("TkDefaultFont", 11, "bold"), padding=9)

    def _build_menu(self) -> None:
        menu = tk.Menu(self)
        file_menu = tk.Menu(menu, tearoff=False)
        file_menu.add_command(label="Compress…", command=lambda: self._set_mode_and_input("compress"))
        file_menu.add_command(label="Extract…", command=lambda: self._set_mode_and_input("extract"))
        file_menu.add_separator(); file_menu.add_command(label="Open Output Folder", command=self.open_output_folder)
        file_menu.add_command(label="Clear", command=self.clear); file_menu.add_separator(); file_menu.add_command(label="Exit", command=self.destroy)
        menu.add_cascade(label="File", menu=file_menu)
        tools = tk.Menu(menu, tearoff=False)
        tools.add_command(label="Generate Password Key", command=self.generate_key); tools.add_command(label="Clear Password", command=self.clear_password)
        menu.add_cascade(label="Tools", menu=tools)
        help_menu = tk.Menu(menu, tearoff=False)
        help_menu.add_command(label="Help", command=self.show_help); help_menu.add_command(label="About", command=self.show_about)
        menu.add_cascade(label="Help", menu=help_menu)
        self.config(menu=menu)

    def _build_toolbar(self) -> None:
        bar = ttk.Frame(self, padding=(10, 8)); bar.pack(fill="x")
        for text, command in (("Compress", lambda: self._set_mode_and_input("compress")), ("Extract", lambda: self._set_mode_and_input("extract")), ("Generate Key", self.generate_key), ("Help", self.show_help), ("About", self.show_about)):
            ttk.Button(bar, text=text, command=command).pack(side="left", padx=3)

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=18); root.pack(fill="both", expand=True)
        header = ttk.Frame(root); header.pack(fill="x", pady=(0, 12))
        ttk.Label(header, text=APP_NAME, style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="NZ v3 • native C++ compression • desktop archive manager", style="Sub.TLabel").pack(anchor="w", pady=(3, 0))
        operations = ttk.LabelFrame(root, text="File", padding=12); operations.pack(fill="x", pady=6)
        ttk.Radiobutton(operations, text="Compress → .nz", variable=self.mode, value="compress", command=self._mode_changed).grid(row=0, column=0, sticky="w", padx=(0, 25))
        ttk.Radiobutton(operations, text="Extract .nz", variable=self.mode, value="extract", command=self._mode_changed).grid(row=0, column=1, sticky="w")
        self._path_row(operations, "Input", self.input_path, self._choose_input, 1); self._path_row(operations, "Output", self.output_path, self._choose_output, 2)
        security = ttk.LabelFrame(root, text="Password / Universal Key", padding=12); security.pack(fill="x", pady=6)
        ttk.Label(security, text="Password").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(security, textvariable=self.password, show="•").grid(row=0, column=1, sticky="ew", padx=8, pady=5)
        ttk.Label(security, text="Confirm").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(security, textvariable=self.confirm_password, show="•").grid(row=1, column=1, sticky="ew", padx=8, pady=5)
        ttk.Button(security, text="Generate Universal Key", command=self.generate_key).grid(row=0, column=2, rowspan=2, padx=8)
        ttk.Label(security, textvariable=self.key_fingerprint, wraplength=650).grid(row=2, column=0, columnspan=3, sticky="w", pady=(7, 0))
        ttk.Label(security, text="Password stays in memory. NZ02 archives are not encrypted yet; this key panel prepares the NZ04 authenticated-encryption design.", style="Sub.TLabel").grid(row=3, column=0, columnspan=3, sticky="w", pady=(5, 0))
        security.columnconfigure(1, weight=1)
        options = ttk.LabelFrame(root, text="Options", padding=12); options.pack(fill="x", pady=6)
        ttk.Checkbutton(options, text="Verify output after operation", variable=self.verify).pack(side="left")
        ttk.Label(options, text="Zstandard • XXH64 • streaming engine").pack(side="right")
        actions = ttk.Frame(root); actions.pack(fill="x", pady=9)
        self.run_button = ttk.Button(actions, text="Start Compression", style="Run.TButton", command=self.start); self.run_button.pack(side="left")
        self.clear_button = ttk.Button(actions, text="Clear", command=self.clear); self.clear_button.pack(side="left", padx=8)
        ttk.Button(actions, text="Open Output Folder", command=self.open_output_folder).pack(side="left")
        ttk.Label(actions, textvariable=self.status).pack(side="right")
        log_frame = ttk.LabelFrame(root, text="Operation Log", padding=8); log_frame.pack(fill="both", expand=True, pady=(3, 0))
        self.log = tk.Text(log_frame, wrap="word", state="disabled", font=("TkFixedFont", 10)); scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set); self.log.pack(side="left", fill="both", expand=True); scroll.pack(side="right", fill="y")
        self.progress = ttk.Progressbar(root, mode="indeterminate"); self.progress.pack(fill="x", pady=(10, 0)); self._log("NZ v3 ready.")
        if not self.engine.get(): self._log("WARNING: native nzcompress engine not found.")

    def _path_row(self, parent, label, variable, command, row):
        ttk.Label(parent, text=label, width=10).grid(row=row, column=0, sticky="w", pady=6)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", padx=8, pady=6); ttk.Button(parent, text="Browse…", command=command).grid(row=row, column=2, pady=6); parent.columnconfigure(1, weight=1)

    def _set_mode_and_input(self, mode): self.mode.set(mode); self._mode_changed(); self._choose_input()
    def _mode_changed(self): self.run_button.configure(text="Start Compression" if self.mode.get() == "compress" else "Start Extraction"); self._auto_output() if self.input_path.get() else None

    def _choose_input(self):
        path = filedialog.askopenfilename(title="Choose file to compress" if self.mode.get() == "compress" else "Choose NZ archive", filetypes=[("NZ archives", "*.nz"), ("All files", "*")] if self.mode.get() == "extract" else None)
        if path: self.input_path.set(path); self._auto_output()

    def _choose_output(self):
        if self.mode.get() == "compress":
            initial = Path(self.input_path.get()).stem + ".nz" if self.input_path.get() else "archive.nz"
            path = filedialog.asksaveasfilename(title="Save NZ archive", defaultextension=".nz", initialfile=initial, filetypes=[("NZ archives", "*.nz"), ("All files", "*")])
        else: path = filedialog.asksaveasfilename(title="Save extracted file", initialfile=Path(self.input_path.get()).stem if self.input_path.get() else "restored-file")
        if path: self.output_path.set(path)

    def _auto_output(self):
        source = Path(self.input_path.get())
        if not source.exists(): return
        self.output_path.set(str(source.with_name(source.name + ".nz")) if self.mode.get() == "compress" else str(source.with_name(source.name[:-3] if source.name.lower().endswith(".nz") else source.stem + "-restored")))

    def generate_key(self):
        if not self.password.get(): messagebox.showwarning("Password required", "Enter a password first."); return
        if self.password.get() != self.confirm_password.get(): messagebox.showerror("Password mismatch", "Password and confirmation do not match."); return
        key = universal_key(self.password.get()); self.key_fingerprint.set("Key fingerprint (SHA-256): " + hashlib.sha256(key).hexdigest()); self._log("Password key generated; password was not logged or saved.")

    def clear_password(self): self.password.set(""); self.confirm_password.set(""); self.key_fingerprint.set("No password key generated")
    def clear(self):
        if self.running: return
        self.input_path.set(""); self.output_path.set(""); self.clear_password(); self.status.set("Ready"); self._log("Cleared.")

    def open_output_folder(self):
        folder = str(Path(self.output_path.get()).parent if self.output_path.get() else Path.cwd())
        try:
            if sys.platform.startswith("linux"): subprocess.Popen(["xdg-open", folder])
            elif sys.platform == "darwin": subprocess.Popen(["open", folder])
            else: os.startfile(folder)  # type: ignore[attr-defined]
        except Exception as exc: messagebox.showerror("Open folder", str(exc))

    def start(self):
        if self.running: return
        engine, source, destination = self.engine.get().strip(), self.input_path.get().strip(), self.output_path.get().strip()
        if not engine or not Path(engine).is_file(): messagebox.showerror("NZ engine not found", "Build the project first or place nzcompress.exe beside the application."); return
        if not source or not Path(source).is_file(): messagebox.showerror("Input required", "Choose an existing input file."); return
        if not destination: self._auto_output(); destination = self.output_path.get().strip()
        if Path(source).resolve() == Path(destination).resolve(): messagebox.showerror("Invalid output", "Input and output must be different files."); return
        if Path(destination).exists() and not messagebox.askyesno("Overwrite", f"Overwrite existing file?\n\n{destination}"): return
        if self.password.get() and self.password.get() != self.confirm_password.get(): messagebox.showerror("Password mismatch", "Password and confirmation do not match."); return
        self.running = True; self.run_button.configure(state="disabled"); self.clear_button.configure(state="disabled"); self.status.set("Working…"); self.progress.start(12)
        threading.Thread(target=self._worker, args=(engine, source, destination), daemon=True).start()

    def _worker(self, engine, source, destination):
        try:
            command = [engine, self.mode.get(), source, destination]; self.events.put(("log", "$ " + " ".join(self._quote(x) for x in command)))
            result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if result.stdout.strip(): self.events.put(("log", result.stdout.strip()))
            if result.returncode != 0: raise RuntimeError(f"NZ engine exited with code {result.returncode}")
            if self.verify.get(): self.events.put(("log", "SHA-256: " + sha256_file(destination) if self.mode.get() == "extract" else f"Archive created: {os.path.getsize(destination):,} bytes"))
            self.events.put(("done", destination))
        except Exception as exc: self.events.put(("error", str(exc)))

    @staticmethod
    def _quote(value): return '"' + value.replace('"', '\\"') + '"' if any(c.isspace() for c in value) else value

    def _poll_events(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "log": self._log(str(value))
                elif kind == "done": self._finish(True, str(value))
                else: self._finish(False, str(value))
        except queue.Empty: pass
        self.after(100, self._poll_events)

    def _finish(self, success, detail):
        self.running = False; self.run_button.configure(state="normal"); self.clear_button.configure(state="normal"); self.progress.stop(); self.status.set("Completed" if success else "Failed")
        self._log("Operation completed successfully." if success else "ERROR: " + detail)
        (messagebox.showinfo if success else messagebox.showerror)("NZ operation", f"Successfully completed.\n\nOutput:\n{detail}" if success else detail)

    def show_help(self): messagebox.showinfo("NZ v3 Help", "File menu and toolbar provide Compress/Extract, output-folder and cleanup actions. The password panel derives a deterministic v3 key fingerprint without storing the password. NZ02 is currently not encrypted; authenticated encryption is reserved for NZ04.")
    def show_about(self): messagebox.showinfo("About Super File Compressor", f"{APP_NAME}\n{VERSION}\n\nNative C++ NZ archive engine\nZstandard compression\nXXH64 integrity verification\nWindows x64 release target")
    def _log(self, text):
        self.log.configure(state="normal"); self.log.insert("end", text + "\n"); self.log.see("end"); self.log.configure(state="disabled")


if __name__ == "__main__": NZGui().mainloop()
