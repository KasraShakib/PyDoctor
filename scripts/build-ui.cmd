@echo off
setlocal

set "PROJECT_ROOT=%~dp0.."
python "%PROJECT_ROOT%\scripts\build-ui.py"
exit /b %ERRORLEVEL%
