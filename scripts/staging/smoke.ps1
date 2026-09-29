[CmdletBinding()]
param(
    [string]$FrontendUrl = "http://127.0.0.1:18080",
    [string]$BackendUrl = "http://127.0.0.1:18000"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if ([Environment]::GetEnvironmentVariable("FITFLOW_SMOKE_ALLOW_FIXTURE_RESET", "Process") -ne "1") {
    throw "Set FITFLOW_SMOKE_ALLOW_FIXTURE_RESET=1 to reset the reserved smoke fixture."
}

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
$composeFile = Join-Path $repositoryRoot "docker-compose.staging.yml"
$composeArguments = @(
    "compose",
    "--project-name", "fitflow-staging",
    "--file", $composeFile
)

$seedArguments = $composeArguments + @(
    "exec", "-T",
    "-e", "FITFLOW_SMOKE_ALLOW_FIXTURE_RESET=1",
    "--workdir", "/app/backend",
    "backend", "python", "-m", "scripts.staging_smoke_seed"
)
& docker @seedArguments
if ($LASTEXITCODE -ne 0) {
    throw "Staging smoke fixture bootstrap failed."
}

& python (Join-Path $PSScriptRoot "mvp_smoke.py") `
    --frontend-url $FrontendUrl `
    --backend-url $BackendUrl
if ($LASTEXITCODE -ne 0) {
    throw "Staging MVP vertical smoke failed."
}
