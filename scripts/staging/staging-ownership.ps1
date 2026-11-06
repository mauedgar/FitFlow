# Shared read-only Docker ownership proof for release and R006 smoke.
# Does not create, modify, remove or reset Docker resources.
Set-StrictMode -Version Latest

function Invoke-StagingCaptured {
    param(
        [Parameter(Mandatory = $true)][string]$Program,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )
    $output = & $Program @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Staging ownership query failed ($LASTEXITCODE): $Program"
    }
    return ($output -join "`n").Trim()
}

# F003: no resumed deployment may trust resource names alone.
function Get-VerifiedStagingOwnership {
    param(
        [string]$ExpectedRevision, [string]$ExpectedProject,
        [string[]]$ComposeArguments, [string]$BackendPort, [string]$FrontendPort
    )
    $allIds = Invoke-StagingCaptured -Program "docker" -Arguments @(
        "ps", "--all", "--quiet", "--no-trunc",
        "--filter", "label=com.docker.compose.project=$ExpectedProject"
    )
    $projectIds = @($allIds -split '\r?\n' | Where-Object { $_ })
    if ($projectIds.Count -ne 4) {
        throw "Expected exactly four qualified containers for the retained project."
    }
    $snapshot = [ordered]@{}
    foreach ($service in @("postgres", "redis", "backend", "frontend")) {
        $id = Invoke-StagingCaptured -Program "docker" -Arguments (
            $ComposeArguments + @("ps", "--all", "--no-trunc", "--quiet", $service)
        )
        if ($id -notmatch '^[a-f0-9]{64}$' -or $projectIds -notcontains $id) {
            throw "Container identity mismatch for $service."
        }
        $json = Invoke-StagingCaptured -Program "docker" -Arguments @(
            "inspect", "--format", "{{json .}}", $id
        )
        $metadata = $json | ConvertFrom-Json
        if ($metadata.Config.Labels.'com.docker.compose.project' -cne $ExpectedProject -or
            $metadata.Config.Labels.'com.docker.compose.service' -cne $service -or
            $metadata.State.Running -ne $true) {
            throw "Container project/service labels or running state mismatch for $service."
        }
        if ($service -in @("backend", "frontend")) {
            if ($metadata.Config.Labels.'org.opencontainers.image.revision' -cne $ExpectedRevision) {
                throw "Image revision mismatch for $service."
            }
            $containerPort = if ($service -eq "backend") { "8000" } else { "8080" }
            $expectedPort = if ($service -eq "backend") { $BackendPort } else { $FrontendPort }
            $port = Invoke-StagingCaptured -Program "docker" -Arguments (
                $ComposeArguments + @("port", $service, $containerPort)
            )
            if ($port -cne "127.0.0.1:$expectedPort") {
                throw "Published loopback port mismatch for $service."
            }
            $snapshot["${service}_image_id"] = [string]$metadata.Image
        } else {
            $volumeService = if ($service -eq "postgres") { "postgres_data" } else { "redis_data" }
            $volumeName = "${ExpectedProject}_$volumeService"
            $mountPath = if ($service -eq "postgres") { "/var/lib/postgresql/data" } else { "/data" }
            $mounts = @($metadata.Mounts)
            if ($mounts.Count -ne 1 -or $mounts[0].Type -cne "volume" -or
                $mounts[0].Name -cne $volumeName -or $mounts[0].Destination -cne $mountPath) {
                throw "Unqualified persistent data mount for $service."
            }
            $v = Invoke-StagingCaptured -Program "docker" -Arguments @(
                "volume", "inspect", "--format", "{{json .}}", $volumeName
            )
            $volume = $v | ConvertFrom-Json
            if ($volume.Labels.'com.docker.compose.project' -cne $ExpectedProject -or
                $volume.Labels.'com.docker.compose.volume' -cne $volumeService) {
                throw "Persistent volume ownership labels mismatch for $service."
            }
        }
    }
    $networkName = "${ExpectedProject}_default"
    $allNetworks = Invoke-StagingCaptured -Program "docker" -Arguments @(
        "network", "ls", "--format", "{{.Name}}"
    )
    $projectNetworks = @($allNetworks -split '\r?\n' | Where-Object {
        $_ -match ("^" + [regex]::Escape($ExpectedProject) + "_")
    })
    if ($projectNetworks.Count -ne 1 -or $projectNetworks[0] -cne $networkName) {
        throw "Unexpected Compose project networks."
    }
    $n = Invoke-StagingCaptured -Program "docker" -Arguments @(
        "network", "inspect", "--format", "{{json .}}", $networkName
    )
    $network = $n | ConvertFrom-Json
    if ($network.Labels.'com.docker.compose.project' -cne $ExpectedProject -or
        $network.Labels.'com.docker.compose.network' -cne "default") {
        throw "Compose network ownership labels mismatch."
    }
    return [pscustomobject]$snapshot
}

function Assert-EmptyStagingProject {
    param([string]$ExpectedProject)
    $containers = Invoke-StagingCaptured -Program "docker" -Arguments @(
        "ps", "--all", "--quiet", "--filter", "label=com.docker.compose.project=$ExpectedProject"
    )
    $volumes = Invoke-StagingCaptured -Program "docker" -Arguments @("volume", "ls", "--quiet")
    $networks = Invoke-StagingCaptured -Program "docker" -Arguments @("network", "ls", "--format", "{{.Name}}")
    $expectedVolumes = @("${ExpectedProject}_postgres_data", "${ExpectedProject}_redis_data")
    if ($containers -or
        @($volumes -split '\r?\n' | Where-Object { $expectedVolumes -contains $_ }).Count -gt 0 -or
        @($networks -split '\r?\n' | Where-Object {
            $_ -match ("^" + [regex]::Escape($ExpectedProject) + "_")
        }).Count -gt 0) {
        throw "Staging project resources appeared after preflight."
    }
}

