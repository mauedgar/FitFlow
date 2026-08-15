$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$ComposeFile = Join-Path $Root "docker-compose.test.yml"
$ComposeArgs = @(
    "compose",
    "--project-name", "fitflow-test",
    "--file", $ComposeFile
)

$Failed = $false

Push-Location $Root
try {
    & docker @ComposeArgs up --build --detach
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host "== pytest =="
    & docker @ComposeArgs exec --no-TTY backend_test python -m pytest tests
    if ($LASTEXITCODE -ne 0) { $Failed = $true }

    Write-Host "`n== Ruff =="
    & docker @ComposeArgs exec --no-TTY backend_test python -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('ruff') else 1)"
    if ($LASTEXITCODE -eq 0) {
        & docker @ComposeArgs exec --no-TTY backend_test python -m ruff check .
        if ($LASTEXITCODE -ne 0) { $Failed = $true }
    }
    else {
        Write-Host "Ruff UNAVAILABLE in backend_test."
    }

    Write-Host "`n== Pyright =="
    & docker @ComposeArgs exec --no-TTY backend_test python -c "import shutil, sys; sys.exit(0 if shutil.which('pyright') else 1)"
    if ($LASTEXITCODE -eq 0) {
        & docker @ComposeArgs exec --no-TTY backend_test pyright .
        if ($LASTEXITCODE -ne 0) { $Failed = $true }
    }
    else {
        Write-Host "Pyright UNAVAILABLE in backend_test."
    }
}
finally {
    Pop-Location
}

if ($Failed) { exit 1 } else { exit 0 }
