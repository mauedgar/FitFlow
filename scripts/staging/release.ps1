[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("deploy", "redeploy", "rollback")]
    [string]$Action,

    [string]$Revision = "HEAD",
    [string]$EnvFile,
    [string]$StateDirectory,
    [switch]$DatabaseForwardCompatible
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

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

function Get-RequiredEnvironmentValue {
    param([Parameter(Mandatory = $true)][string]$Name)

    $value = [Environment]::GetEnvironmentVariable($Name, "Process")
    if ([string]::IsNullOrWhiteSpace($value)) {
        throw "$Name must be supplied through the process environment or -EnvFile."
    }
    return $value
}

function Import-EnvironmentFile {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Environment file does not exist: $Path"
    }

    foreach ($line in Get-Content -LiteralPath $Path) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#")) {
            continue
        }
        $parts = $trimmed.Split("=", 2)
        if ($parts.Count -ne 2 -or [string]::IsNullOrWhiteSpace($parts[0])) {
            throw "Invalid environment entry in $Path."
        }
        [Environment]::SetEnvironmentVariable($parts[0], $parts[1], "Process")
    }
}

function Get-Sha256 {
    param([Parameter(Mandatory = $true)][string]$Value)

    $bytes = [Text.Encoding]::UTF8.GetBytes($Value)
    $hash = [Security.Cryptography.SHA256]::HashData($bytes)
    return [Convert]::ToHexString($hash).ToLowerInvariant()
}

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
if ($EnvFile) {
    $EnvFile = (Resolve-Path $EnvFile).Path
    Import-EnvironmentFile -Path $EnvFile
}

if ([string]::IsNullOrWhiteSpace($StateDirectory)) {
    $StateDirectory = Join-Path ([Environment]::GetFolderPath("LocalApplicationData")) "FitFlow/staging"
}
$StateDirectory = [IO.Path]::GetFullPath($StateDirectory)
[IO.Directory]::CreateDirectory($StateDirectory) | Out-Null
$statePath = Join-Path $StateDirectory "deployment-state.json"

$resolvedRevision = (& git -C $repositoryRoot rev-parse --verify "$Revision`^{commit}").Trim()
if ($LASTEXITCODE -ne 0 -or $resolvedRevision -notmatch "^[0-9a-f]{40}$") {
    throw "Revision is not a resolvable Git commit: $Revision"
}
$headRevision = (& git -C $repositoryRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $headRevision -ne $resolvedRevision) {
    throw "The checked-out HEAD must equal the requested revision. Use an isolated worktree for $resolvedRevision."
}
if (& git -C $repositoryRoot status --porcelain --untracked-files=no) {
    throw "Tracked files are dirty; refusing to build an unidentified release."
}

$requiredNames = @("POSTGRES_PASSWORD", "SECRET_KEY", "BACKEND_CORS_ORIGINS")
$configurationMaterial = foreach ($name in $requiredNames) {
    $value = Get-RequiredEnvironmentValue -Name $name
    "$name=$value"
}
$configurationHash = Get-Sha256 -Value ($configurationMaterial -join "`n")

$previousState = $null
if (Test-Path -LiteralPath $statePath -PathType Leaf) {
    $previousState = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
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
$composeArguments = @("compose")
if ($EnvFile) {
    $composeArguments += @("--env-file", $EnvFile)
}
$composeArguments += @("--project-name", "fitflow-staging", "--file", (Join-Path $repositoryRoot "docker-compose.staging.yml"))

Invoke-Checked -Program "docker" -Arguments ($composeArguments + @("config", "--quiet"))

$databaseRevisionBefore = $null
if ($Action -eq "rollback") {
    $databaseRevisionBefore = Invoke-CapturedChecked -Program "docker" -Arguments (
        $composeArguments + @("exec", "-T", "backend", "alembic", "current")
    )

    Invoke-Checked -Program "docker" -Arguments ($composeArguments + @("build", "backend"))
    $targetHead = Invoke-CapturedChecked -Program "docker" -Arguments (
        $composeArguments + @("run", "--rm", "--no-deps", "backend", "alembic", "heads")
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

$backendPort = [Environment]::GetEnvironmentVariable("STAGING_BACKEND_PORT", "Process")
if ([string]::IsNullOrWhiteSpace($backendPort)) { $backendPort = "18000" }
$frontendPort = [Environment]::GetEnvironmentVariable("STAGING_FRONTEND_PORT", "Process")
if ([string]::IsNullOrWhiteSpace($frontendPort)) { $frontendPort = "18080" }

$live = Invoke-RestMethod -Uri "http://127.0.0.1:$backendPort/health/live" -TimeoutSec 10
$ready = Invoke-RestMethod -Uri "http://127.0.0.1:$backendPort/health/ready" -TimeoutSec 10
$frontend = Invoke-WebRequest -Uri "http://127.0.0.1:$frontendPort/" -TimeoutSec 10
if ($live.status -ne "alive" -or $ready.status -ne "ready" -or $frontend.StatusCode -ne 200) {
    throw "Post-release verification failed."
}

$databaseRevisionAfter = Invoke-CapturedChecked -Program "docker" -Arguments (
    $composeArguments + @("exec", "-T", "backend", "alembic", "current")
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
    project = "fitflow-staging"
    verified_at = [DateTimeOffset]::UtcNow.ToString("o")
}
$state | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding utf8
$state | ConvertTo-Json
