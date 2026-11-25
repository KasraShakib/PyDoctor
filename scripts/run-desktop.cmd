@echo off
setlocal

rem Launch the interim stdlib desktop interface. No Node.js, Rust, or network
rem access is required. The React + Tauri interface remains the long-term target.

set "PROJECT_ROOT=%~dp0.."
set "PYTHONPATH=%PROJECT_ROOT%\engine\python\src"

python "%PROJECT_ROOT%\apps\desktop\pydoctor_ui.py"
exit /b %ERRORLEVEL%
