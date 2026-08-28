[CmdletBinding()]
param(
  [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
  [string]$ApiUrl = $env:NEXT_PUBLIC_API_URL,
  [int]$Port = 3000
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($ApiUrl)) { throw "Define NEXT_PUBLIC_API_URL or pass -ApiUrl." }

$env:NEXT_PUBLIC_API_URL = $ApiUrl
Push-Location $ProjectRoot
try {
  npm --workspace @wtg/web run dev -- --hostname 127.0.0.1 -p $Port
  if ($LASTEXITCODE -ne 0) { throw "Next.js failed to start." }
}
finally {
  Pop-Location
}
