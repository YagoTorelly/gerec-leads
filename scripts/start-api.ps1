[CmdletBinding()]
param(
  [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
  [string]$MongoUri = $env:MONGODB_URI,
  [string]$MongoDatabase = $env:MONGODB_DATABASE,
  [string]$AppSecret = $env:APP_SECRET,
  [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($MongoUri)) { throw "Define MONGODB_URI or pass -MongoUri." }
if ([string]::IsNullOrWhiteSpace($MongoDatabase)) { throw "Define MONGODB_DATABASE or pass -MongoDatabase." }
if ([string]::IsNullOrWhiteSpace($AppSecret)) { throw "Define APP_SECRET or pass -AppSecret." }

$apiRoot = Join-Path $ProjectRoot "apps\api"
$env:MONGODB_URI = $MongoUri
$env:MONGODB_DATABASE = $MongoDatabase
$env:APP_SECRET = $AppSecret

Push-Location $apiRoot
try {
  python -m uvicorn gerec_api.main:create_app --factory --host 127.0.0.1 --port $Port --reload
}
finally {
  Pop-Location
}
