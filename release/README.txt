PyDoctor 0.3.0 - Portable Windows Build
=======================================

Your Python environment, understood.

WHAT THIS IS
------------
PyDoctor is a read-only diagnostics tool for Windows Python environments. It
discovers interpreters, inspects installed packages, explains tracebacks, reads
notebook/kernel metadata, and produces dry-run repair plans.

This folder is portable: no installer, no admin rights, no network access.

QUICK START
-----------
1. Double-click PyDoctor-UI.exe  (React interface, native WebView2 window)
2. Or run PyDoctor.exe           (Tkinter fallback, standard library only)

In the app:
  - Pick an interpreter from the dropdown (discovered automatically) or paste a
    python.exe path.
  - Optionally pick a project directory.
  - Choose a mode chip: Full report, Packages, Notebooks, Explain error, Repair
    plan, Discover, or Compare.
  - Press Run check (or Ctrl+Enter).

Top bar:
  - Sun/moon button switches between light and dark themes.
  - FA/EN button switches between Persian (right-to-left) and English.
  - Both choices are remembered between launches.

REQUIREMENTS
------------
- Windows 10/11, 64-bit.
- PyDoctor-UI.exe needs the Microsoft Edge WebView2 runtime. It is preinstalled
  on Windows 11 and on most updated Windows 10 systems.
- PyDoctor.exe needs nothing beyond Windows and the bundled runtime.

SAFETY
------
PyDoctor never executes the interpreters it inspects, never imports their
packages, never runs pip, never activates an environment, and never changes
PATH, the Registry, or project files. Repair plans are dry-run only.

Reports contain local paths. Review them before sharing.

SELF-CHECK
----------
To verify the packaged React app on this machine:

  set PYDOCTOR_SELF_CHECK_OUT=%TEMP%\pyd.json
  PyDoctor-UI.exe
  type %TEMP%\pyd.json

Expected fields: brand=true, mode=true, layout=true, controls=true,
logo=true, bridge=true, and report_scope="python_discovery".

VERIFY INTEGRITY
----------------
  certutil -hashfile PyDoctor-UI.exe SHA256
  certutil -hashfile PyDoctor.exe SHA256

Compare with SHA256SUMS.txt.

NOTE
----
The executables are unsigned. Windows SmartScreen may show a warning the first
time you run them. Choose "More info" then "Run anyway" only if you trust this
build.
