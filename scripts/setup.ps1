$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot

if (-not (Test-Path -LiteralPath ".venv\Scripts\python.exe")) {
    py -m venv .venv
}

& ".venv\Scripts\python.exe" -m pip install --upgrade pip
& ".venv\Scripts\python.exe" -m pip install -r requirements.txt

if (-not (Test-Path -LiteralPath ".env")) {
    $SecretKey = & ".venv\Scripts\python.exe" -c "import secrets; print(secrets.token_hex(32))"
    $EnvironmentFile = (Get-Content -LiteralPath ".env.example" -Raw).Replace(
        "replace-with-a-long-random-value",
        $SecretKey.Trim()
    )
    Set-Content -LiteralPath ".env" -Value $EnvironmentFile -Encoding UTF8
}

ollama pull dolphin3:8b
ollama create airo-rp -f Modelfile

Write-Host ""
Write-Host "AIRO ist eingerichtet." -ForegroundColor Green
Write-Host "Starte die App mit: .\scripts\run.ps1"
