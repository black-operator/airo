$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackupRoot = Join-Path $ProjectRoot "backups"
$Stamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$Destination = Join-Path $BackupRoot $Stamp
New-Item -ItemType Directory -Path $Destination -Force | Out-Null

mongodump --db airo --out (Join-Path $Destination "mongodb")
Copy-Item -LiteralPath (Join-Path $ProjectRoot "app\static\uploads") -Destination (Join-Path $Destination "uploads") -Recurse -Force
Write-Host "Backup gespeichert: $Destination" -ForegroundColor Green
