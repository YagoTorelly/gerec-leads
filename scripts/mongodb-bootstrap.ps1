[CmdletBinding()]
param(
  [Parameter(Mandatory = $false)]
  [string]$MongoUri = $env:MONGODB_URI,

  [Parameter(Mandatory = $false)]
  [string]$MongoDatabase = $env:MONGODB_DATABASE
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($MongoUri)) {
  throw "Defina MONGODB_URI ou informe -MongoUri."
}

if ([string]::IsNullOrWhiteSpace($MongoDatabase)) {
  throw "Defina MONGODB_DATABASE ou informe -MongoDatabase."
}

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$apiRoot = Join-Path $repositoryRoot "apps\api"
$previousPythonPath = $env:PYTHONPATH

try {
  $env:MONGODB_URI = $MongoUri
  $env:MONGODB_DATABASE = $MongoDatabase
  $env:PYTHONPATH = Join-Path $apiRoot "src"
  Push-Location $apiRoot
  python -c "import os; from pymongo import MongoClient; from gerec_api.infrastructure.mongo.bootstrap import ensure_schema; client = MongoClient(os.environ['MONGODB_URI']); ensure_schema(client[os.environ['MONGODB_DATABASE']]); client.close()"
  if ($LASTEXITCODE -ne 0) { throw "O bootstrap MongoDB falhou com c\u00f3digo $LASTEXITCODE." }
  Write-Host "Schema MongoDB aplicado para '$MongoDatabase'."
}
finally {
  Pop-Location
  $env:PYTHONPATH = $previousPythonPath
}
