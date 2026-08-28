[CmdletBinding()]
param(
  [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
  [string]$MongoUri = $env:MONGODB_URI,
  [string]$MongoDatabase = $env:MONGODB_DATABASE,
  [string]$AppSecret = $env:APP_SECRET,
  [string]$ApiUrl = $env:NEXT_PUBLIC_API_URL,
  [int]$ApiPort = 8000,
  [int]$WebPort = 3000
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($MongoUri)) { throw "Define MONGODB_URI or pass -MongoUri." }
if ([string]::IsNullOrWhiteSpace($MongoDatabase)) { throw "Define MONGODB_DATABASE or pass -MongoDatabase." }
if ([string]::IsNullOrWhiteSpace($AppSecret)) { throw "Define APP_SECRET or pass -AppSecret." }
if ([string]::IsNullOrWhiteSpace($ApiUrl)) { $ApiUrl = "http://127.0.0.1:$ApiPort" }

$powershell = (Get-Command powershell.exe).Source
& (Join-Path $PSScriptRoot "start-mongodb.ps1") -ProjectRoot $ProjectRoot
& (Join-Path $PSScriptRoot "mongodb-bootstrap.ps1") -MongoUri $MongoUri -MongoDatabase $MongoDatabase

function Start-LocalProcess {
  param(
    [string]$ScriptPath,
    [string]$Arguments,
    [hashtable]$Environment
  )

  $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
  $startInfo.FileName = $powershell
  $startInfo.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`" -ProjectRoot `"$ProjectRoot`" $Arguments"
  $startInfo.WorkingDirectory = $ProjectRoot
  $startInfo.UseShellExecute = $false
  $startInfo.CreateNoWindow = $true
  foreach ($entry in $Environment.GetEnumerator()) {
    $startInfo.EnvironmentVariables[$entry.Key] = $entry.Value
  }

  $process = [System.Diagnostics.Process]::Start($startInfo)
  if ($null -eq $process) { throw "Failed to start $ScriptPath." }
}

$backendEnvironment = @{
  MONGODB_URI = $MongoUri
  MONGODB_DATABASE = $MongoDatabase
  APP_SECRET = $AppSecret
}
Start-LocalProcess -ScriptPath (Join-Path $PSScriptRoot "start-api.ps1") -Arguments "-Port $ApiPort" -Environment $backendEnvironment
Start-LocalProcess -ScriptPath (Join-Path $PSScriptRoot "start-web.ps1") -Arguments "-ApiUrl `"$ApiUrl`" -Port $WebPort" -Environment @{ NEXT_PUBLIC_API_URL = $ApiUrl }

Write-Output "MongoDB, API and web started in background processes."
