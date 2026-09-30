# AIRO

AIRO is a private, local-first character chat application built with Flask, MongoDB, and Ollama. It lets you create AI characters, switch between user personas, upload avatars, and keep persistent role-play or general chat conversations on your own computer.

> [!IMPORTANT]
> AIRO is designed for trusted local use on `127.0.0.1`. It has not been hardened for public internet deployment. Do not expose the development server, MongoDB, or Ollama directly to the internet.

## Features

- Local signup and login with Argon2 password hashing
- Character editor with personality, scenario, speaking style, example dialogue, and custom instructions
- Multiple user personas with independent identity and relationship context
- Persistent conversations stored in MongoDB
- Token-by-token response streaming from Ollama
- Character and persona snapshots for stable ongoing conversations
- Safe JPG, PNG, and WebP avatar processing
- Responsive monochrome interface with light and dark themes
- Collapsible chat details and recent conversations in the sidebar
- Local backup script for MongoDB and uploaded avatars
- No cloud account, analytics, or external AI API required

## Technology

- Python 3.12
- Flask 3
- MongoDB with PyMongo
- Ollama with a customized Dolphin 3 8B model
- Jinja templates, vanilla JavaScript, and custom CSS
- Waitress for the normal local server

## Requirements

- Windows 10 or Windows 11
- Python 3.12 with the `py` launcher
- MongoDB installed locally and running
- Ollama installed locally
- Enough disk space for the Ollama model
- A modern browser
- An NVIDIA GPU with approximately 8 GB VRAM is recommended, but Ollama may also use CPU or shared memory at lower speed

## Quick start

Open PowerShell in the project directory and run:

```powershell
.\scripts\setup.ps1
```

The setup script creates `.venv`, installs the pinned Python dependencies, creates `.env` with a random secret when needed, downloads `dolphin3:8b`, and builds the customized local model `airo-rp` from `Modelfile`.

Start AIRO:

```powershell
.\scripts\run.ps1
```

Then open <http://127.0.0.1:5000> and create the first local account.

For manual installation, configuration, testing, and model commands, see [Installation](docs/INSTALLATION.md).

## Project structure

```text
AIRO/
|-- app/
|   |-- services/          # Ollama, prompting, and avatar processing
|   |-- static/            # CSS, JavaScript, favicon, local uploads
|   |-- templates/         # Jinja interface templates
|   |-- auth.py            # Signup, login, and user session handling
|   |-- characters.py      # Character CRUD
|   |-- personas.py        # Persona CRUD
|   |-- chat.py            # Conversations and response streaming
|   `-- db.py              # MongoDB helpers and indexes
|-- docs/                  # Detailed documentation
|-- scripts/               # Setup, start, and backup scripts
|-- tests/                 # Pytest test suite
|-- Modelfile              # AIRO Ollama model definition
|-- requirements.txt       # Runtime dependencies
|-- requirements-dev.txt   # Runtime and test dependencies
|-- run.py                 # Flask development entry point
`-- wsgi.py                # Waitress/WSGI entry point
```

See [Architecture](docs/ARCHITECTURE.md) for the application modules, data model, prompt assembly, and security boundaries.

## Configuration

AIRO reads configuration from `.env`. Never commit that file. Copy `.env.example` and replace the secret key:

```powershell
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

| Variable | Default | Purpose |
| --- | --- | --- |
| `SECRET_KEY` | none | Signs Flask sessions and CSRF tokens |
| `MONGO_URI` | `mongodb://127.0.0.1:27017/` | Local MongoDB connection |
| `MONGO_DB` | `airo` | Database name |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama API address |
| `OLLAMA_MODEL` | `airo-rp` | Model used for conversations |
| `MAX_CONTENT_LENGTH` | `8388608` | Maximum request/upload size in bytes |

## Development

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe .\run.py
```

## Backups

With MongoDB Database Tools installed, run:

```powershell
.\scripts\backup.ps1
```

The script creates a timestamped MongoDB and avatar backup under `backups/`. That directory is excluded from Git.

## Troubleshooting

Common setup, MongoDB, Ollama, model, and browser problems are covered in [Troubleshooting](docs/TROUBLESHOOTING.md).

## Privacy and security

- Uploaded images, users, characters, personas, and messages stay on the local machine.
- `.env`, `.venv`, uploads, backups, caches, and compiled Python files are excluded from Git.
- AIRO binds to `127.0.0.1` by default.
- MongoDB and Ollama should also remain bound to localhost.
- Use a unique `SECRET_KEY` even for local use.

## License

AIRO is released under [The Unlicense](LICENSE), matching the license already selected for this repository. The Ollama base model is downloaded separately and remains subject to its own upstream license.
