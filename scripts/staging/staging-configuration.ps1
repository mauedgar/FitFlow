# Dot-source only in release.ps1 and smoke.ps1; no side effects at import.
Set-StrictMode -Version Latest

function Import-StagingEnvironmentFile {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Explicit staging environment file does not exist."
    }
    foreach ($line in Get-Content -LiteralPath $Path) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#")) { continue }
        $parts = $trimmed.Split("=", 2)
        if ($parts.Count -ne 2 -or [string]::IsNullOrWhiteSpace($parts[0])) {
            throw "Malformed staging environment entry."
        }
        [Environment]::SetEnvironmentVariable($parts[0], $parts[1], "Process")
    }
}

function Get-StagingEnvValue {
    param([string]$Name, [string]$Default, [switch]$Required)
    $value = [Environment]::GetEnvironmentVariable($Name, "Process")
    if ([string]::IsNullOrEmpty($value)) {
        if ($Required) { throw "$Name is required in explicit staging environment." }
        return $Default
    }
    return $value
}

function Resolve-StagingConfiguration {
    param([Parameter(Mandatory = $true)][string]$ProjectName)

    # One canonical ordered material for the release receipt and R006 verifier.
    $values = [ordered]@{
        POSTGRES_DB = (Get-StagingEnvValue -Name "POSTGRES_DB" -Default "fitflow_staging")
        POSTGRES_USER = (Get-StagingEnvValue -Name "POSTGRES_USER" -Default "fitflow_staging")
        POSTGRES_PASSWORD = (Get-StagingEnvValue -Name "POSTGRES_PASSWORD" -Required)
        SECRET_KEY = (Get-StagingEnvValue -Name "SECRET_KEY" -Required)
        BACKEND_CORS_ORIGINS = (Get-StagingEnvValue -Name "BACKEND_CORS_ORIGINS" -Required)
        LOG_LEVEL = (Get-StagingEnvValue -Name "LOG_LEVEL" -Default "INFO")
        STAGING_BACKEND_PORT = (Get-StagingEnvValue -Name "STAGING_BACKEND_PORT" -Required)
        STAGING_FRONTEND_PORT = (Get-StagingEnvValue -Name "STAGING_FRONTEND_PORT" -Required)
        FITFLOW_RELEASE_IMAGE_NAMESPACE = "fitflow-$ProjectName"
        VITE_API_BASE_URL = (Get-StagingEnvValue -Name "VITE_API_BASE_URL" -Default "/api/v1")
        FITFLOW_TIMEZONE = (Get-StagingEnvValue -Name "FITFLOW_TIMEZONE" -Default "America/Argentina/Buenos_Aires")
    }
    $ports = @{}
    foreach ($portName in @("STAGING_BACKEND_PORT", "STAGING_FRONTEND_PORT")) {
        $port = 0
        if (-not [int]::TryParse([string]$values[$portName], [ref]$port) -or
            $port -lt 1024 -or $port -gt 65535 -or $port -in @(18000, 18080)) {
            throw "$portName must be a non-privileged port other than legacy 18000/18080."
        }
        $ports[$portName] = $port
        $values[$portName] = [string]$port
    }
    if ($ports.STAGING_BACKEND_PORT -eq $ports.STAGING_FRONTEND_PORT) {
        throw "Backend and frontend host ports must differ numerically."
    }
    $frontendTimezone = [Environment]::GetEnvironmentVariable("VITE_FITFLOW_TIMEZONE", "Process")
    if (-not [string]::IsNullOrEmpty($frontendTimezone) -and
        $frontendTimezone -cne $values.FITFLOW_TIMEZONE) {
        throw "VITE_FITFLOW_TIMEZONE must equal FITFLOW_TIMEZONE."
    }
    try { [void][TimeZoneInfo]::FindSystemTimeZoneById([string]$values.FITFLOW_TIMEZONE) }
    catch { throw "FITFLOW_TIMEZONE must be a valid IANA timezone." }

    [Environment]::SetEnvironmentVariable("VITE_FITFLOW_TIMEZONE", $values.FITFLOW_TIMEZONE, "Process")
    foreach ($entry in $values.GetEnumerator()) {
        [Environment]::SetEnvironmentVariable([string]$entry.Key, [string]$entry.Value, "Process")
    }
    [Environment]::SetEnvironmentVariable("COMPOSE_DISABLE_ENV_FILE", "1", "Process")
    $material = @($values.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join "`n"
    $bytes = [Text.Encoding]::UTF8.GetBytes($material)
    $digest = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)).ToLowerInvariant()
    return [pscustomobject]@{
        Values = $values
        Sha256 = $digest
    }
}
