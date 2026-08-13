$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$Backend = Join-Path $Root "backend"
$VenvPython = Join-Path $Backend ".venv_backend\Scripts\python.exe"

if (Test-Path $VenvPython) {
    $Python = $VenvPython
} else {
    $Python = "python"
}

Push-Location $Backend
try {
    & $Python -m pytest @args
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
