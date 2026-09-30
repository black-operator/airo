# Troubleshooting

## `py` is not found

Install Python 3.12 from python.org and enable the Python launcher. Verify it with `py --version`.

## PowerShell blocks a script

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Run the setup or start script again. This setting applies only to the current PowerShell process.

## MongoDB is unavailable

```powershell
Get-Service MongoDB
```

Start it from an administrator PowerShell window when necessary:

```powershell
Start-Service MongoDB
```

Confirm that `.env` uses `MONGO_URI=mongodb://127.0.0.1:27017/`.

## Ollama is offline

Run `ollama serve`, then test the API in another terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```

## `airo-rp` is missing

```powershell
ollama pull dolphin3:8b
ollama create airo-rp -f Modelfile
ollama list
```

The `.env` value must be `OLLAMA_MODEL=airo-rp`.

## Port 5000 is already in use

```powershell
Get-NetTCPConnection -LocalPort 5000 -State Listen
```

Stop the old AIRO process in its terminal, or run a temporary development instance:

```powershell
$env:FLASK_APP = "wsgi"
.\.venv\Scripts\python.exe -m flask run --port 5001
```

## CSS or JavaScript changes do not appear

Restart AIRO when using Waitress, then hard-refresh the browser with `Ctrl+F5`.

## Repeated favicon error

Current versions include `app/static/favicon.svg` and an explicit `/favicon.ico` route. Update the repository and restart the server. A regression test covers this behavior.

## Avatar upload fails

- Use JPG, PNG, or WebP.
- Keep the request below `MAX_CONTENT_LENGTH`.
- Verify that `app/static/uploads` exists and is writable.

## Run diagnostics

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```
