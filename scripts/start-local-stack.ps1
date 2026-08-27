param(
  [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
  [int]$DockerTimeoutSeconds = 180,
  [int]$WebPort = 3000
)

$ErrorActionPreference = "Stop"
$logDirectory = Join-Path $ProjectRoot ".local\logs"
$null = New-Item -ItemType Directory -Force -Path $logDirectory
$logFile = Join-Path $logDirectory "startup.log"

function Write-StartupLog([string]$Message) {
  $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
  Add-Content -LiteralPath $logFile -Value $line
}

try {
  Write-StartupLog "Iniciando stack local em $ProjectRoot"
  $dockerDesktop = Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"
  if (Test-Path -LiteralPath $dockerDesktop) {
    Start-Process -FilePath $dockerDesktop -WindowStyle Hidden
    Write-StartupLog "Docker Desktop solicitado"
  }
  $deadline = (Get-Date).AddSeconds($DockerTimeoutSeconds)
  do {
    docker info *> $null
    if ($LASTEXITCODE -eq 0) { break }
    Start-Sleep -Seconds 5
  } while ((Get-Date) -lt $deadline)
  docker info *> $null
  if ($LASTEXITCODE -ne 0) { throw "Docker daemon não respondeu dentro do limite." }
  Write-StartupLog "Docker daemon disponível"
  Push-Location $ProjectRoot
  try {
    npm run supabase:start *>> $logFile
    if ($LASTEXITCODE -ne 0) { throw "supabase:start falhou" }
    npm run env:local *>> $logFile
    if ($LASTEXITCODE -ne 0) { throw "env:local falhou" }
    $webLog = Join-Path $logDirectory "web.log"
    $webCommand = "npm --workspace @wtg/web run dev -- --hostname 0.0.0.0 -p $WebPort >> `"$webLog`" 2>&1"
    Start-Process -FilePath "cmd.exe" -ArgumentList "/d", "/c", $webCommand -WorkingDirectory $ProjectRoot -WindowStyle Hidden
    Write-StartupLog "Frontend iniciado na porta $WebPort"
  }
  finally { Pop-Location }
}
catch {
  Write-StartupLog "ERRO: $($_.Exception.Message)"
  exit 1
}
