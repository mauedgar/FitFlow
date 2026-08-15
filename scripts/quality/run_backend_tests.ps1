$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$ComposeFile = Join-Path $Root "docker-compose.test.yml"
$ComposeArgs = @(
    "compose",
    "--project-name", "fitflow-test",
    "--file", $ComposeFile
)

Push-Location $Root
try {
    & docker @ComposeArgs up --build --detach
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    & docker @ComposeArgs exec --no-TTY backend_test python -m pytest tests @args
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
