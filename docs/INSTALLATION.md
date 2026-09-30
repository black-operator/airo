# Installation guide

This guide describes a clean Windows installation of AIRO.

## 1. Install the prerequisites

Install:

- Python 3.12, including the Python launcher (`py`)
- MongoDB Community Server
- Ollama for Windows
- MongoDB Database Tools if you want to use the backup script

Verify everything in PowerShell:

```powershell
py --version
ollama --version
Get-Service MongoDB
```

MongoDB should report `Running`. If the service exists but is stopped, open PowerShell as administrator and run `Start-Service MongoDB`.

## 2. Clone the repository

```powershell
git clone https://github.com/black-operator/airo.git
Set-Location airo
```

## 3. Run the automatic setup

```powershell
.\scripts\setup.ps1
```

This may take a while because Ollama downloads the base model.

If PowerShell blocks local scripts for the current process:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\setup.ps1
```

The policy change lasts only for the current PowerShell process.

## 4. Configure AIRO

The setup script creates `.env` with a random secret when the file does not exist. To configure it manually instead:

```powershell
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

Copy the generated value into `SECRET_KEY` in `.env`.

```dotenv
SECRET_KEY=replace-with-a-long-random-value
MONGO_URI=mongodb://127.0.0.1:27017/
MONGO_DB=airo
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=airo-rp
MAX_CONTENT_LENGTH=8388608
```

## 5. Start AIRO

```powershell
.\scripts\run.ps1
```

Open <http://127.0.0.1:5000>. The first registered account is a normal local account. AIRO does not send email or use an external identity provider.

## Manual setup

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
ollama pull dolphin3:8b
ollama create airo-rp -f Modelfile
.\.venv\Scripts\python.exe -m waitress --listen=127.0.0.1:5000 wsgi:app
```

## Updating an existing clone

```powershell
git pull
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
ollama create airo-rp -f Modelfile
```

Restart AIRO afterward.

## Development setup

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe .\run.py
```

`run.py` enables Flask debug mode and is for development only. The normal `run.ps1` uses Waitress.
