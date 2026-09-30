$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot

if (-not (Test-Path -LiteralPath ".venv\Scripts\python.exe")) {
    throw "Das venv fehlt. Fuehre zuerst .\scripts\setup.ps1 aus."
}

try {
    Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 2 | Out-Null
} catch {
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 2
}

Write-Host "AIRO laeuft unter http://127.0.0.1:5000" -ForegroundColor Green
& ".venv\Scripts\python.exe" -m waitress --listen=127.0.0.1:5000 wsgi:app
