@echo off
setlocal

rem Run the standard-library test suites without requiring PowerShell script
rem execution to be enabled. Mirrors scripts\run-tests.ps1.

set "PROJECT_ROOT=%~dp0.."
set "ENGINE_ROOT=%PROJECT_ROOT%\engine\python"
set "DESKTOP_TESTS=%PROJECT_ROOT%\apps\desktop\tests"
set "NATIVE_TESTS=%PROJECT_ROOT%\apps\desktop_native\tests"
set "VENV_PYTHON=%ENGINE_ROOT%\.venv\Scripts\python.exe"

if exist "%VENV_PYTHON%" (
    set "PYTHON=%VENV_PYTHON%"
) else (
    set "PYTHON=python"
)

set "OLD_PYTHONPATH=%PYTHONPATH%"
set "PYTHONPATH=%ENGINE_ROOT%\src;%PROJECT_ROOT%\apps\desktop;%PROJECT_ROOT%\apps\desktop_native"

set "TEST_EXIT_CODE=0"

pushd "%ENGINE_ROOT%"
"%PYTHON%" -m unittest discover -s tests -p "test_*.py" -v
if errorlevel 1 set "TEST_EXIT_CODE=1"
popd

if exist "%DESKTOP_TESTS%" (
    pushd "%PROJECT_ROOT%\apps\desktop"
    "%PYTHON%" -m unittest discover -s tests -p "test_*.py" -v
    if errorlevel 1 set "TEST_EXIT_CODE=1"
    popd
)

if exist "%NATIVE_TESTS%" (
    pushd "%PROJECT_ROOT%\apps\desktop_native"
    "%PYTHON%" -m unittest discover -s tests -p "test_*.py" -v
    if errorlevel 1 set "TEST_EXIT_CODE=1"
    popd
)

if defined OLD_PYTHONPATH (
    set "PYTHONPATH=%OLD_PYTHONPATH%"
) else (
    set "PYTHONPATH="
)

exit /b %TEST_EXIT_CODE%
