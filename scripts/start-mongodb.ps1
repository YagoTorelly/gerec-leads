[CmdletBinding()]
param(
  [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
)

$ErrorActionPreference = "Stop"

Push-Location $ProjectRoot
try {
  docker compose -f infra/mongodb/docker-compose.yml up -d --wait
  if ($LASTEXITCODE -ne 0) { throw "MongoDB replica set failed to start." }
}
finally {
  Pop-Location
}
