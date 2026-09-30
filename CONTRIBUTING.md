# Contributing

AIRO is a small local-first project. Contributions should prioritize correctness, maintainability, privacy, and a restrained interface.

## Workflow

1. Create or activate the Python 3.12 virtual environment.
2. Install `requirements-dev.txt`.
3. Keep MongoDB and Ollama bound to localhost.
4. Make a focused change.
5. Add or update tests for behavior changes and bug fixes.
6. Run the full test suite.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

## Expectations

- Preserve the Flask application-factory structure.
- Keep database access and ownership checks on the server.
- Never expose Ollama or MongoDB directly to browser code.
- Validate uploads by decoding them, not only by trusting extensions.
- Escape or sanitize user- and model-generated HTML.
- Do not commit `.env`, uploads, backups, databases, virtual environments, or caches.
- Prefer small JavaScript modules and semantic server-rendered HTML over a large frontend framework.
- Respect reduced-motion preferences and keyboard accessibility.

Keep commits focused and explain the observable behavior change. Never include local secrets or private conversation data.
