[CmdletBinding()]
param(
    [string]$ProjectName,
    [string]$StateDirectory,
    [string]$EnvFile,
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
. (Join-Path $PSScriptRoot "staging-configuration.ps1")
. (Join-Path $PSScriptRoot "staging-ownership.ps1")
# The seed and HTTP test implementation must be from the exact reviewed release.
$sourceSha = (& git -C $repositoryRoot rev-parse HEAD) -join "`n"
if ($LASTEXITCODE -ne 0 -or $sourceSha.Trim() -cne $Revision) {
    throw "Smoke source HEAD mismatch; refusing fixture reset."
}
$sourceStatus = (& git -C $repositoryRoot status --porcelain --untracked-files=all) -join "`n"
if ($LASTEXITCODE -ne 0 -or $sourceStatus) {
    throw "Smoke source is not clean; refusing fixture reset."
}
$ignoredBuildInputs = (& git -C $repositoryRoot ls-files --others --ignored --exclude-standard -- backend frontend) -join "`n"
if ($LASTEXITCODE -ne 0 -or $ignoredBuildInputs) {
    throw "Smoke source has ignored/untracked build inputs; refusing fixture reset."
}
$composeFile = Join-Path $repositoryRoot "docker-compose.staging.yml"
[Environment]::SetEnvironmentVariable("FITFLOW_COMPOSE_PROJECT", $ProjectName, "Process")
[Environment]::SetEnvironmentVariable("FITFLOW_RELEASE_IMAGE_NAMESPACE", "fitflow-$ProjectName", "Process")
[Environment]::SetEnvironmentVariable("FITFLOW_REVISION", $Revision, "Process")
[Environment]::SetEnvironmentVariable("COMPOSE_DISABLE_ENV_FILE", "1", "Process")
$composeArguments = @("compose")
if ($EnvFile) {
    if (-not (Test-Path -LiteralPath $EnvFile -PathType Leaf)) {
        throw "Explicit smoke -EnvFile does not exist."
    }
    $EnvFile = (Resolve-Path -LiteralPath $EnvFile).Path
    Import-StagingEnvironmentFile -Path $EnvFile
    $composeArguments += @("--env-file", $EnvFile)
}
$composeArguments += @("--project-name", $ProjectName, "--file", $composeFile)

# No fixture writes before verifying the precise released project, services and ports.
if ([string]::IsNullOrWhiteSpace($StateDirectory)) {
    $StateDirectory = Join-Path ([Environment]::GetFolderPath("LocalApplicationData")) "FitFlow/staging/$ProjectName"
}
$statePath = Join-Path ([IO.Path]::GetFullPath($StateDirectory)) "deployment-state.json"
if (-not (Test-Path -LiteralPath $statePath -PathType Leaf)) {
    throw "Missing isolated release receipt."
}
$state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
if ($state.project -cne $ProjectName -or $state.current_revision -cne $Revision -or
    -not $state.configuration_sha256 -or -not $state.database_revision -or
    $state.migrations_downgraded -ne $false) {
    throw "Release receipt identity or migration safety mismatch."
}
# F002: same ordered inputs and normalization as release.ps1, not merely
# the presence of a plausible hash in deployment-state.json.
$effectiveConfiguration = Resolve-StagingConfiguration -ProjectName $ProjectName
if ([string]$state.configuration_sha256 -cne [string]$effectiveConfiguration.Sha256) {
    throw "Staging smoke configuration SHA-256 does not match the recorded release."
}

# F001 IR002: the very same Docker labels, volumes, network and image
# identity proof used by R005 is mandatory immediately before fixture writes.
if ($state.schema_version -ne 2 -or
    $state.git_tree_sha -notmatch '^[0-9a-f]{40}$' -or
    -not $state.backend_image_id -or -not $state.frontend_image_id) {
    throw "Smoke requires a complete schema-v2 ownership receipt."
}
$sourceTree = (& git -C $repositoryRoot rev-parse 'HEAD^{tree}') -join "`n"
if ($LASTEXITCODE -ne 0 -or $sourceTree.Trim() -cne $state.git_tree_sha) {
    throw "Smoke source tree differs from the released source tree."
}
foreach ($pair in @(
    @{ Service = "backend"; Url = $BackendUrl; Port = $effectiveConfiguration.Values.STAGING_BACKEND_PORT },
    @{ Service = "frontend"; Url = $FrontendUrl; Port = $effectiveConfiguration.Values.STAGING_FRONTEND_PORT }
)) {
    $uri = $null
    if (-not [Uri]::TryCreate($pair.Url, [UriKind]::Absolute, [ref]$uri) -or
        $uri.Scheme -cne "http" -or $uri.Host -cne "127.0.0.1" -or
        $uri.UserInfo -or $uri.AbsolutePath -cne "/" -or $uri.Query -or $uri.Fragment -or
        [string]$uri.Port -cne [string]$pair.Port) {
        throw "$($pair.Service) smoke origin must match the recorded loopback port."
    }
}
$runtime = Get-VerifiedStagingOwnership -ExpectedRevision $Revision `
    -ExpectedProject $ProjectName -ComposeArguments $composeArguments `
    -BackendPort $effectiveConfiguration.Values.STAGING_BACKEND_PORT `
    -FrontendPort $effectiveConfiguration.Values.STAGING_FRONTEND_PORT
if ($runtime.backend_image_id -cne $state.backend_image_id -or
    $runtime.frontend_image_id -cne $state.frontend_image_id) {
    throw "Smoke image IDs differ from the released images; refusing fixture reset."
}
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
