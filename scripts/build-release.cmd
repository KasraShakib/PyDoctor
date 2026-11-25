@echo off
setlocal

rem Full release build: UI bundle, executables, portable folder, and zip.

set "PROJECT_ROOT=%~dp0.."
cd /d "%PROJECT_ROOT%"

call scripts\build-ui.cmd
if errorlevel 1 exit /b %ERRORLEVEL%

call scripts\build-exe.cmd
if errorlevel 1 exit /b %ERRORLEVEL%

python scripts\build-release.py
exit /b %ERRORLEVEL%
