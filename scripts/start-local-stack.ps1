[CmdletBinding()]
param(
  [string]$ProjectRoot,
  [string]$MongoUri = $env:MONGODB_URI,
  [string]$MongoDatabase = $env:MONGODB_DATABASE,
  [string]$AppSecret = $env:APP_SECRET,
  [string]$ApiUrl = $env:NEXT_PUBLIC_API_URL,
  [int]$ApiPort = 8000,
  [int]$WebPort = 3000
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
  $ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
$logDirectory = Join-Path $ProjectRoot ".local\logs"
$null = New-Item -ItemType Directory -Force -Path $logDirectory

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
    [hashtable]$Environment,
    [string]$LogPath,
    [switch]$PublicWebEnvironment
  )

  $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
  $startInfo.FileName = (Get-Command cmd.exe).Source
  $scriptInvocation = "`"$powershell`" -NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`" -ProjectRoot `"$ProjectRoot`" $Arguments"
  $startInfo.Arguments = "/d /c `"`"$scriptInvocation`" > `"$LogPath`" 2>&1`""
  $startInfo.WorkingDirectory = $ProjectRoot
  $startInfo.UseShellExecute = $false
  $startInfo.CreateNoWindow = $true
  if ($PublicWebEnvironment) {
    $safeEnvironmentNames = @(
      "ALLUSERSPROFILE", "APPDATA", "COMSPEC", "HOMEDRIVE", "HOMEPATH", "LOCALAPPDATA",
      "NUMBER_OF_PROCESSORS", "OS", "PATH", "PATHEXT", "PROCESSOR_ARCHITECTURE",
      "PROCESSOR_IDENTIFIER", "PROGRAMDATA", "PROGRAMFILES", "PROGRAMFILES(X86)", "PROGRAMW6432",
      "PSMODULEPATH", "SYSTEMDRIVE", "SYSTEMROOT", "TEMP", "TMP", "USERDOMAIN",
      "USERDOMAIN_ROAMINGPROFILE", "USERNAME", "USERPROFILE", "WINDIR"
    )
    $startInfo.EnvironmentVariables.Clear()
    foreach ($name in $safeEnvironmentNames) {
      $value = [Environment]::GetEnvironmentVariable($name)
      if (-not [string]::IsNullOrWhiteSpace($value)) {
        $startInfo.EnvironmentVariables[$name] = $value
      }
    }
  }
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
$apiLog = Join-Path $logDirectory "api.log"
$webLog = Join-Path $logDirectory "web.log"
Start-LocalProcess -ScriptPath (Join-Path $PSScriptRoot "start-api.ps1") -Arguments "-Port $ApiPort" -Environment $backendEnvironment -LogPath $apiLog
Start-LocalProcess -ScriptPath (Join-Path $PSScriptRoot "start-web.ps1") -Arguments "-ApiUrl `"$ApiUrl`" -Port $WebPort" -Environment @{ NEXT_PUBLIC_API_URL = $ApiUrl } -LogPath $webLog -PublicWebEnvironment

Write-Output "MongoDB, API and web started in background processes. Logs: $apiLog, $webLog"
