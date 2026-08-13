$ErrorActionPreference = "Continue"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$Backend = Join-Path $Root "backend"
$VenvPython = Join-Path $Backend ".venv_backend\Scripts\python.exe"
$Python = if (Test-Path $VenvPython) { $VenvPython } else { "python" }

$Failed = $false

Write-Host "== pytest =="
Push-Location $Backend
& $Python -m pytest
if ($LASTEXITCODE -ne 0) { $Failed = $true }

Write-Host "`n== Ruff =="
& $Python -m ruff check .
if ($LASTEXITCODE -ne 0) {
    Write-Host "Ruff FAIL or UNAVAILABLE. Verify installation before interpreting."
    $Failed = $true
}

Write-Host "`n== Pyright =="
$Pyright = Get-Command pyright -ErrorAction SilentlyContinue
if ($Pyright) {
    & pyright .
    if ($LASTEXITCODE -ne 0) { $Failed = $true }
} else {
    Write-Host "Pyright UNAVAILABLE on PATH."
    $Failed = $true
}

Pop-Location

if ($Failed) { exit 1 } else { exit 0 }
