[CmdletBinding()]
param(
  [string]$ProjectRoot,
  [switch]$RemoveVolumes
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
  $ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
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
