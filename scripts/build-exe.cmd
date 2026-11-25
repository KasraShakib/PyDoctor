@echo off
setlocal

rem Build the standalone Windows executables.
rem Requires PyInstaller and a built React bundle in apps\desktop-ui\dist.

set "PROJECT_ROOT=%~dp0.."
cd /d "%PROJECT_ROOT%"

echo [1/2] Building PyDoctor.exe (Tkinter interface)...
python -m PyInstaller packaging\pydoctor-tk.spec --noconfirm
if errorlevel 1 exit /b %ERRORLEVEL%

echo [2/2] Building PyDoctor-UI.exe (React + WebView2 interface)...
python -m PyInstaller packaging\pydoctor-ui.spec --noconfirm
if errorlevel 1 exit /b %ERRORLEVEL%

echo Build complete. Output is in dist\.
exit /b 0
