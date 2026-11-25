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
$testExitCode = 0
Push-Location $engineRoot
try {
    $env:PYTHONPATH = (Join-Path $engineRoot "src") + ";" + (Join-Path $projectRoot "apps\desktop") + ";" + (Join-Path $projectRoot "apps\desktop_native")
    & $python -m unittest discover -s tests -p "test_*.py" -v
    if ($LASTEXITCODE -ne 0) { $testExitCode = 1 }
} finally {
    $env:PYTHONPATH = $previousPythonPath
    Pop-Location
}

foreach ($suite in @("apps\desktop", "apps\desktop_native")) {
    $suitePath = Join-Path $projectRoot $suite
    if (Test-Path -LiteralPath (Join-Path $suitePath "tests")) {
        Push-Location $suitePath
        try {
            $env:PYTHONPATH = (Join-Path $engineRoot "src") + ";" + (Join-Path $projectRoot "apps\desktop") + ";" + (Join-Path $projectRoot "apps\desktop_native")
            & $python -m unittest discover -s tests -p "test_*.py" -v
            if ($LASTEXITCODE -ne 0) { $testExitCode = 1 }
        } finally {
            $env:PYTHONPATH = $previousPythonPath
            Pop-Location
        }
    }
}
exit $testExitCode
