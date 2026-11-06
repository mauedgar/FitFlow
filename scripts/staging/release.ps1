[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("preflight", "deploy", "redeploy", "rollback")]
    [string]$Action,

    [string]$ProjectName,
    [string]$Revision = "HEAD",
    [string]$EnvFile,
    [string]$StateDirectory,
    [switch]$DatabaseForwardCompatible
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if ([string]::IsNullOrWhiteSpace($ProjectName) -or $ProjectName -cnotmatch '^[a-z][a-z0-9_-]{2,50}$') {
    throw "Explicit -ProjectName is required for an isolated staging project."
}
if ($ProjectName -in @("fitflow-staging", "fitflow")) {
    throw "Refusing retained historical/shared Compose project."
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Program,
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed ($LASTEXITCODE): $Program $($Arguments -join ' ')"
    }
}

function Invoke-CapturedChecked {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Program,
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    $output = & $Program @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed ($LASTEXITCODE): $Program $($Arguments -join ' ')"
    }
    return ($output -join "`n").Trim()
}

. (Join-Path $PSScriptRoot "staging-configuration.ps1")

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
if ($EnvFile) {
    $EnvFile = (Resolve-Path $EnvFile).Path
    Import-StagingEnvironmentFile -Path $EnvFile
}

if ([string]::IsNullOrWhiteSpace($StateDirectory)) {
    $StateDirectory = Join-Path ([Environment]::GetFolderPath("LocalApplicationData")) "FitFlow/staging/$ProjectName"
}
$StateDirectory = [IO.Path]::GetFullPath($StateDirectory)
$statePath = Join-Path $StateDirectory "deployment-state.json"

$resolvedRevision = Invoke-CapturedChecked -Program "git" -Arguments @(
    "-C", $repositoryRoot, "rev-parse", "--verify", "$Revision`^{commit}"
)
if ($resolvedRevision -notmatch "^[0-9a-f]{40}$") {
    throw "Revision is not a resolvable Git commit: $Revision"
}
$headRevision = Invoke-CapturedChecked -Program "git" -Arguments @("-C", $repositoryRoot, "rev-parse", "HEAD")
if ($headRevision -ne $resolvedRevision) {
    throw "The checked-out HEAD must equal the requested revision. Use an isolated worktree for $resolvedRevision."
}
$worktreeStatus = Invoke-CapturedChecked -Program "git" -Arguments @(
    "-C", $repositoryRoot, "status", "--porcelain", "--untracked-files=all"
)
if ($worktreeStatus) {
    throw "Tracked or untracked files are dirty; refusing to build an unidentified release."
}

$ignoredBuildInputs = Invoke-CapturedChecked -Program "git" -Arguments @(
    "-C", $repositoryRoot, "ls-files", "--others", "--ignored", "--exclude-standard", "--", "backend", "frontend"
)
if ($ignoredBuildInputs) {
    throw "Git-ignored files exist inside Docker-copied source trees; refusing to build an unidentified release."
}

$normalizedConfiguration = Resolve-StagingConfiguration -ProjectName $ProjectName
$configurationValues = $normalizedConfiguration.Values
$configurationHash = $normalizedConfiguration.Sha256

$previousState = $null
if (Test-Path -LiteralPath $statePath -PathType Leaf) {
    $previousState = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
}

if ($null -ne $previousState -and [string]$previousState.project -cne $ProjectName) {
    throw "Deployment state belongs to another project."
}
if ($Action -eq "deploy" -and $null -ne $previousState) {
    throw "Deploy refuses previous state; use an explicitly reviewed redeploy."
}
if ($Action -eq "redeploy") {
    if ($null -eq $previousState -or $previousState.current_revision -ne $resolvedRevision) {
        throw "Redeploy requires deployment-state.json to identify the same current revision."
    }
}
if ($Action -eq "rollback") {
    if (-not $DatabaseForwardCompatible) {
        throw "Rollback requires -DatabaseForwardCompatible after explicit schema compatibility review."
    }
    if ($null -eq $previousState -or $previousState.current_revision -eq $resolvedRevision) {
        throw "Rollback requires a recorded, different current revision."
    }
}

[Environment]::SetEnvironmentVariable("FITFLOW_REVISION", $resolvedRevision, "Process")
[Environment]::SetEnvironmentVariable("FITFLOW_COMPOSE_PROJECT", $ProjectName, "Process")
$composeArguments = @("compose")
if ($EnvFile) {
    $composeArguments += @("--env-file", $EnvFile)
}
$composeArguments += @("--project-name", $ProjectName, "--file", (Join-Path $repositoryRoot "docker-compose.staging.yml"))

Invoke-Checked -Program "docker" -Arguments ($composeArguments + @("config", "--quiet"))
# Read-only identity inventory before Docker build/up or any Alembic migration.
$existingContainers = Invoke-CapturedChecked -Program "docker" -Arguments @(
    "ps", "--all", "--quiet", "--filter", "label=com.docker.compose.project=$ProjectName"
)
$allVolumes = Invoke-CapturedChecked -Program "docker" -Arguments @("volume", "ls", "--quiet")
$volumeNames = @($allVolumes -split '\r?\n')
$expectedVolumes = @("${ProjectName}_postgres_data", "${ProjectName}_redis_data")
$foundVolumes = @($expectedVolumes | Where-Object { $volumeNames -contains $_ })
$allNetworks = Invoke-CapturedChecked -Program "docker" -Arguments @("network", "ls", "--format", "{{.Name}}")
$networkNames = @($allNetworks -split '\r?\n')
$projectNetworks = @($networkNames | Where-Object { $_ -match ("^" + [regex]::Escape($ProjectName) + "_") })
if ($Action -in @("preflight", "deploy")) {
    if ($null -ne $previousState -or $existingContainers -or $foundVolumes.Count -gt 0 -or $projectNetworks.Count -gt 0) {
        throw "Isolated first release refuses existing project state, containers, volumes or networks."
    }
}
if ($Action -in @("redeploy", "rollback")) {
    if (-not $existingContainers -or $foundVolumes.Count -ne 2 -or $projectNetworks.Count -lt 1) {
        throw "Existing release requires current project containers and both named volumes."
    }
}
if ($Action -eq "preflight") {
    [ordered]@{
        result = "CONFIG_PREFLIGHT_ONLY"
        project = $ProjectName
        revision = $resolvedRevision
        configuration_sha256 = $configurationHash
        data_effect = "NONE"
        staging_runtime_qualified = $false
    } | ConvertTo-Json
    return
}

$databaseRevisionBefore = $null
if ($Action -eq "rollback") {
    $databaseRevisionBefore = Invoke-CapturedChecked -Program "docker" -Arguments (
        $composeArguments + @("exec", "-T", "--workdir", "/app/backend", "backend", "alembic", "current")
    )

    Invoke-Checked -Program "docker" -Arguments ($composeArguments + @("build", "backend"))
    $targetHead = Invoke-CapturedChecked -Program "docker" -Arguments (
        $composeArguments + @("run", "--rm", "--no-deps", "--workdir", "/app/backend", "backend", "alembic", "heads")
    )
    $databaseRevisionId = ($databaseRevisionBefore -split "\s+")[0]
    $targetRevisionId = ($targetHead -split "\s+")[0]
    if ($databaseRevisionId -ne $targetRevisionId) {
        throw "Unsafe automated rollback: live DB revision '$databaseRevisionId' differs from target head '$targetRevisionId'. No downgrade was attempted."
    }
}

Invoke-Checked -Program "docker" -Arguments ($composeArguments + @("build"))
$upArguments = @("up", "--detach", "--wait")
if ($Action -eq "redeploy") {
    $upArguments += "--force-recreate"
}
Invoke-Checked -Program "docker" -Arguments ($composeArguments + $upArguments)

$backendPort = $configurationValues.STAGING_BACKEND_PORT
$frontendPort = $configurationValues.STAGING_FRONTEND_PORT

$live = Invoke-RestMethod -Uri "http://127.0.0.1:$backendPort/health/live" -TimeoutSec 10
$ready = Invoke-RestMethod -Uri "http://127.0.0.1:$backendPort/health/ready" -TimeoutSec 10
$frontend = Invoke-WebRequest -Uri "http://127.0.0.1:$frontendPort/" -TimeoutSec 10
if ($live.status -ne "alive" -or $ready.status -ne "ready" -or $frontend.StatusCode -ne 200) {
    throw "Post-release verification failed."
}

$databaseRevisionAfter = Invoke-CapturedChecked -Program "docker" -Arguments (
    $composeArguments + @("exec", "-T", "--workdir", "/app/backend", "backend", "alembic", "current")
)

$priorRevision = $null
if ($null -ne $previousState) {
    $priorRevision = $previousState.current_revision
}
$state = [ordered]@{
    schema_version = 1
    action = $Action
    current_revision = $resolvedRevision
    previous_revision = $priorRevision
    configuration_sha256 = $configurationHash
    database_revision = $databaseRevisionAfter
    database_revision_before = $databaseRevisionBefore
    migrations_downgraded = $false
    project = $ProjectName
    verified_at = [DateTimeOffset]::UtcNow.ToString("o")
}
[IO.Directory]::CreateDirectory($StateDirectory) | Out-Null
$state | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding utf8
$state | ConvertTo-Json
