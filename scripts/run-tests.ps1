$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$engineRoot = Join-Path $projectRoot "engine\python"
$venvPython = Join-Path $engineRoot ".venv\Scripts\python.exe"

if (Test-Path -LiteralPath $venvPython) {
    $python = $venvPython
} else {
    $python = (Get-Command python -ErrorAction Stop).Source
}

$previousPythonPath = $env:PYTHONPATH
$testExitCode = 1
Push-Location $engineRoot
try {
    $env:PYTHONPATH = Join-Path $engineRoot "src"
    & $python -m unittest discover -s tests -p "test_*.py" -v
    $testExitCode = $LASTEXITCODE
} finally {
    $env:PYTHONPATH = $previousPythonPath
    Pop-Location
}
exit $testExitCode
