[CmdletBinding()]
param(
    [string]$ProjectName,
    [string]$Revision,
    [string]$FrontendUrl,
    [string]$BackendUrl
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if ([string]::IsNullOrWhiteSpace($ProjectName) -or
    $ProjectName -cnotmatch '^[a-z][a-z0-9_-]{2,50}$' -or
    $ProjectName -in @("fitflow-staging", "fitflow")) {
    throw "Explicit non-legacy -ProjectName is required."
}
if ($Revision -cnotmatch '^[0-9a-f]{40}$') {
    throw "Explicit 40-character full -Revision is required."
}
if (-not $FrontendUrl -or -not $BackendUrl) {
    throw "Explicit loopback frontend/backend URLs are required."
}
if ([Environment]::GetEnvironmentVariable("FITFLOW_SMOKE_ALLOW_FIXTURE_RESET", "Process") -ne "1") {
    throw "Set FITFLOW_SMOKE_ALLOW_FIXTURE_RESET=1 to reset the reserved smoke fixture."
}

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
$composeFile = Join-Path $repositoryRoot "docker-compose.staging.yml"
$composeArguments = @(
    "compose",
    "--project-name", $ProjectName,
    "--file", $composeFile
)

# No fixture writes before verifying the precise released project, services and ports.
$statePath = Join-Path (Join-Path ([Environment]::GetFolderPath("LocalApplicationData")) "FitFlow/staging/$ProjectName") "deployment-state.json"
if (-not (Test-Path -LiteralPath $statePath -PathType Leaf)) {
    throw "Missing isolated release receipt."
}
$state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
if ($state.project -cne $ProjectName -or $state.current_revision -cne $Revision) {
    throw "Release receipt identity mismatch."
}
function Assert-StagingService {
    param([string]$Service, [string]$ContainerPort, [string]$Url)
    $uri = $null
    if (-not [Uri]::TryCreate($Url, [UriKind]::Absolute, [ref]$uri) -or
        $uri.Scheme -cne "http" -or $uri.Host -cne "127.0.0.1" -or
        $uri.UserInfo -or $uri.AbsolutePath -cne "/" -or $uri.Query -or $uri.Fragment) {
        throw "$Service URL must be a plain IPv4 loopback HTTP origin."
    }
    $published = (& docker @composeArguments port $Service $ContainerPort) -join "`n"
    if ($LASTEXITCODE -ne 0 -or $published.Trim() -cne "127.0.0.1:$($uri.Port)") {
        throw "$Service URL must match the selected project's exact published port."
    }
    $containerId = (& docker @composeArguments ps --quiet $Service) -join "`n"
    if ($LASTEXITCODE -ne 0 -or -not $containerId.Trim()) {
        throw "Missing $Service container."
    }
    $labelsJson = (& docker inspect --format '{{json .Config.Labels}}' $containerId.Trim()) -join "`n"
    if ($LASTEXITCODE -ne 0) {
        throw "Cannot verify $Service labels."
    }
    $labels = $labelsJson | ConvertFrom-Json
    if ($labels.'com.docker.compose.project' -cne $ProjectName -or
        $labels.'org.opencontainers.image.revision' -cne $Revision) {
        throw "$Service container identity mismatch."
    }
}
Assert-StagingService -Service "backend" -ContainerPort "8000" -Url $BackendUrl
Assert-StagingService -Service "frontend" -ContainerPort "8080" -Url $FrontendUrl
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
