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
$logDirectory = Join-Path $ProjectRoot ".local\logs"
$null = New-Item -ItemType Directory -Force -Path $logDirectory

if ([string]::IsNullOrWhiteSpace($MongoUri)) { throw "Define MONGODB_URI or pass -MongoUri." }
if ([string]::IsNullOrWhiteSpace($MongoDatabase)) { throw "Define MONGODB_DATABASE or pass -MongoDatabase." }
if ([string]::IsNullOrWhiteSpace($AppSecret)) { throw "Define APP_SECRET or pass -AppSecret." }
if ([string]::IsNullOrWhiteSpace($ApiUrl)) { $ApiUrl = "http://127.0.0.1:$ApiPort" }

$powershell = (Get-Command powershell.exe).Source
& (Join-Path $PSScriptRoot "start-mongodb.ps1") -ProjectRoot $ProjectRoot
& (Join-Path $PSScriptRoot "mongodb-bootstrap.ps1") -MongoUri $MongoUri -MongoDatabase $MongoDatabase

$apiLog = Join-Path $logDirectory "api.log"
$apiArguments = "-NoProfile -ExecutionPolicy Bypass -File `"$PSScriptRoot\start-api.ps1`" -ProjectRoot `"$ProjectRoot`" -MongoUri `"$MongoUri`" -MongoDatabase `"$MongoDatabase`" -AppSecret `"$AppSecret`" -Port $ApiPort"
Start-Process -FilePath $powershell -ArgumentList $apiArguments -WorkingDirectory $ProjectRoot -WindowStyle Hidden -RedirectStandardOutput $apiLog -RedirectStandardError $apiLog

$webLog = Join-Path $logDirectory "web.log"
$webArguments = "-NoProfile -ExecutionPolicy Bypass -File `"$PSScriptRoot\start-web.ps1`" -ProjectRoot `"$ProjectRoot`" -ApiUrl `"$ApiUrl`" -Port $WebPort"
Start-Process -FilePath $powershell -ArgumentList $webArguments -WorkingDirectory $ProjectRoot -WindowStyle Hidden -RedirectStandardOutput $webLog -RedirectStandardError $webLog

Write-Output "MongoDB, API and web started. Logs: $logDirectory"
