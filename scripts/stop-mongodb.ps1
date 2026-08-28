[CmdletBinding()]
param(
  [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
  [switch]$RemoveVolumes
)

$ErrorActionPreference = "Stop"
$arguments = @("compose", "-f", "infra/mongodb/docker-compose.yml", "down")
if ($RemoveVolumes) { $arguments += "--volumes" }

Push-Location $ProjectRoot
try {
  & docker @arguments
  if ($LASTEXITCODE -ne 0) { throw "MongoDB replica set failed to stop." }
}
finally {
  Pop-Location
}
