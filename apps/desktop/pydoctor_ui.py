"""Runnable stdlib desktop interface for PyDoctor.

This is the interim M5 desktop layer. It renders the engine's JSON reports with
Tkinter so the product runs without Node.js, Rust, or network access. The
React + Tauri interface remains the long-term target.
"""

import queue
import sys
import threading
import traceback
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

ROOT = Path(__file__).resolve().parents[2]
ENGINE_SRC = ROOT / "engine" / "python" / "src"
if str(ENGINE_SRC) not in sys.path:
    sys.path.insert(0, str(ENGINE_SRC))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from pydoctor import __version__  # noqa: E402
from pydoctor.environment_report import build_environment_report  # noqa: E402
from pydoctor.error_explainer import explain_error, read_traceback  # noqa: E402
from pydoctor.notebooks import inspect_notebooks  # noqa: E402
from pydoctor.package_diagnostics import inspect_packages  # noqa: E402
from pydoctor.repair import build_repair_plan  # noqa: E402

import ui_model  # noqa: E402


def _icon_path() -> Path | None:
    """Return the bundled icon path for both source and frozen execution."""
    base = Path(getattr(sys, "_MEIPASS", ROOT))
    for name in ("icon-tk.ico", "icon.ico"):
        candidate = base / "assets" / name
        if candidate.is_file():
            return candidate
    return None


class PyDoctorApp:
    """Small, keyboard-friendly viewer for engine reports."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.last_report: dict | None = None
        root.title(f"PyDoctor {__version__}")
        icon = _icon_path()
        if icon is not None:
            try:
                root.iconbitmap(default=str(icon))
            except tk.TclError:
                pass
        root.geometry("1040x720")
        root.minsize(760, 520)
        self._results: queue.Queue = queue.Queue()
        self._build()
        self.root.after(100, self._poll)
        self.root.bind("<F5>", lambda _event: self.run_full())
        self.root.bind("<Control-o>", lambda _event: self._browse_interpreter())

    def _build(self) -> None:
        inputs = ttk.Frame(self.root, padding=8)
        inputs.pack(fill="x")
        ttk.Label(inputs, text="Interpreter:").grid(row=0, column=0, sticky="w")
        self.interpreter_var = tk.StringVar(value=sys.executable)
        ttk.Entry(inputs, textvariable=self.interpreter_var, width=72).grid(
            row=0, column=1, sticky="we", padx=4
        )
        ttk.Button(inputs, text="Browse...", command=self._browse_interpreter).grid(
            row=0, column=2
        )
        ttk.Label(inputs, text="Project:").grid(row=1, column=0, sticky="w", pady=(4, 0))
        self.project_var = tk.StringVar()
        ttk.Entry(inputs, textvariable=self.project_var, width=72).grid(
            row=1, column=1, sticky="we", padx=4, pady=(4, 0)
        )
        ttk.Button(inputs, text="Browse...", command=self._browse_project).grid(
            row=1, column=2, pady=(4, 0)
        )
        inputs.columnconfigure(1, weight=1)

        actions = ttk.Frame(self.root, padding=(8, 0))
        actions.pack(fill="x")
        for text, command in (
            ("Full report (F5)", self.run_full),
            ("Packages", self.run_packages),
            ("Notebooks", self.run_notebooks),
            ("Explain error", self.run_error),
            ("Repair plan", self.run_repair),
        ):
            ttk.Button(actions, text=text, command=command).pack(side="left", padx=2)

        self.status = tk.StringVar(value="Ready. Select an interpreter and run a report.")
        ttk.Label(self.root, textvariable=self.status, padding=(8, 6)).pack(fill="x")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.summary = self._text_tab("Summary")
        self.details = self._text_tab("Details")
        self.raw = self._text_tab("Raw JSON")

    def _text_tab(self, title: str) -> tk.Text:
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=title)
        text = tk.Text(frame, wrap="word", font=("Consolas", 10), undo=False)
        scrollbar = ttk.Scrollbar(frame, command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return text

    def _set_text(self, widget: tk.Text, value: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", value)
        widget.configure(state="disabled")

    def _browse_interpreter(self) -> None:
        path = filedialog.askopenfilename(
            title="Select a Python interpreter",
            filetypes=[
                ("Python executable", "python.exe"),
                ("Executables", "*.exe"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self.interpreter_var.set(path)

    def _browse_project(self) -> None:
        path = filedialog.askdirectory(title="Select a project directory")
        if path:
            self.project_var.set(path)

    def _interpreter(self) -> str:
        value = self.interpreter_var.get().strip()
        if not value:
            raise ValueError("Select an interpreter path first.")
        return value

    def _run_async(self, label: str, operation) -> None:
        self.status.set(f"Running {label}...")

        def worker() -> None:
            try:
                report = operation()
            except Exception as exc:  # UI boundary: report, never crash silently.
                message = f"{type(exc).__name__}: {exc}\n\n{traceback.format_exc()}"
                self._results.put(("error", message))
                return
            self._results.put(("ok", report, label))

        threading.Thread(target=worker, daemon=True).start()

    def _poll(self) -> None:
        """Drain worker results on the Tk main thread."""
        try:
            while True:
                item = self._results.get_nowait()
                if item[0] == "ok":
                    _, report, label = item
                    self._show(report, label)
                else:
                    self._fail(item[1])
        except queue.Empty:
            pass
        self.root.after(100, self._poll)

    def _show(self, report: dict, label: str) -> None:
        self.last_report = report
        self._set_text(self.summary, ui_model.describe(report))
        self._set_text(self.details, ui_model.details(report))
        self._set_text(self.raw, ui_model.pretty(report))
        self.status.set(f"{label} complete.")

    def _fail(self, message: str) -> None:
        self.status.set("Failed. See the error dialog.")
        messagebox.showerror("PyDoctor", message)

    def run_full(self) -> None:
        try:
            interpreter = self._interpreter()
        except ValueError as exc:
            messagebox.showinfo("PyDoctor", str(exc))
            return
        project = self.project_var.get().strip() or None
        self._run_async(
            "full report",
            lambda: build_environment_report(interpreter, project).to_dict(),
        )

    def run_packages(self) -> None:
        try:
            interpreter = self._interpreter()
        except ValueError as exc:
            messagebox.showinfo("PyDoctor", str(exc))
            return
        self._run_async("package report", lambda: inspect_packages(interpreter).to_dict())

    def run_notebooks(self) -> None:
        try:
            interpreter = self._interpreter()
        except ValueError as exc:
            messagebox.showinfo("PyDoctor", str(exc))
            return
        target = self.project_var.get().strip() or interpreter
        self._run_async(
            "notebook report",
            lambda: inspect_notebooks(target, interpreter).to_dict(),
        )

    def run_error(self) -> None:
        path = filedialog.askopenfilename(
            title="Select a traceback text file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        interpreter = self.interpreter_var.get().strip() or None

        def operation() -> dict:
            text, issues = read_traceback(path)
            if text is None:
                raise OSError(issues[0].message if issues else "Traceback could not be read.")
            return explain_error(
                text,
                source=path,
                intended_interpreter=interpreter,
                extra_issues=issues,
            ).to_dict()

        self._run_async("error explanation", operation)

    def run_repair(self) -> None:
        if not self.last_report:
            messagebox.showinfo("PyDoctor", "Run a report first, then request a repair plan.")
            return
        report = self.last_report
        self._run_async("repair plan", lambda: build_repair_plan(report, "desktop").to_dict())


def main() -> None:
    root = tk.Tk()
    PyDoctorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
