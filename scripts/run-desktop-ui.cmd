@echo off
setlocal

rem Launch the React interface inside the native WebView2 shell.
rem Requires a built bundle in apps\desktop-ui\dist.

set "PROJECT_ROOT=%~dp0.."
set "PYTHONPATH=%PROJECT_ROOT%\engine\python\src"

python "%PROJECT_ROOT%\apps\desktop_native\app.py"
exit /b %ERRORLEVEL%
