[CmdletBinding()]
param(
  [string]$ProjectRoot,
  [string]$MongoUri = $env:MONGODB_URI,
  [string]$MongoDatabase = $env:MONGODB_DATABASE,
  [string]$AppSecret = $env:APP_SECRET,
  [int]$BatchSize = 100
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
  $ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

if ([string]::IsNullOrWhiteSpace($MongoUri)) { throw "Define MONGODB_URI or pass -MongoUri." }
if ([string]::IsNullOrWhiteSpace($MongoDatabase)) { throw "Define MONGODB_DATABASE or pass -MongoDatabase." }
if ([string]::IsNullOrWhiteSpace($AppSecret)) { throw "Define APP_SECRET or pass -AppSecret." }

$apiRoot = Join-Path $ProjectRoot "apps\api"
$env:MONGODB_URI = $MongoUri
$env:MONGODB_DATABASE = $MongoDatabase
$env:APP_SECRET = $AppSecret
$env:OUTBOX_BATCH_SIZE = $BatchSize

Push-Location $apiRoot
try {
  python -m gerec_api.automation.outbox_worker
}
finally {
  Pop-Location
}
