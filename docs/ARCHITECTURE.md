# Architecture

AIRO is a server-rendered Flask application optimized for private local use. It deliberately avoids a large JavaScript framework and communicates with Ollama only through the Flask backend.

## Request flow

```text
Browser
  -> Flask routes and CSRF validation
  -> MongoDB persistence
  -> prompt builder
  -> local Ollama /api/chat stream
  -> newline-delimited JSON response
  -> browser streaming UI
```

The browser never receives direct MongoDB or Ollama credentials.

## Application modules

- `app/__init__.py`: application factory, extensions, template filters, error handlers, and sidebar context
- `app/auth.py`: account creation, login, logout, Argon2 verification, and user loading
- `app/characters.py`: character creation, editing, avatar handling, and deletion
- `app/personas.py`: persona creation, editing, avatar handling, and deletion
- `app/chat.py`: conversation creation, history loading, message streaming, and model status
- `app/main.py`: dashboard, profile settings, and favicon route
- `app/db.py`: database access, ObjectId parsing, indexes, and conversation de-duplication
- `app/services/prompting.py`: system prompt construction and context-window trimming
- `app/services/ollama_client.py`: Ollama health checks, generation lock, and streamed requests
- `app/services/avatars.py`: image validation, metadata removal, square crop, resize, and WebP output

## MongoDB collections

### `users`

Local account identity, display name, avatar filename, Argon2 password hash, and timestamps.

### `characters`

Character name, description, greeting, personality, speaking style, scenario, example dialogue, extra instructions, reply length, avatar, ownership, and timestamps.

### `personas`

User role information such as name, pronouns, appearance, personality, background, relationship context, extra instructions, avatar, ownership, and timestamps.

### `conversations`

Ownership, character and persona references, snapshots of both definitions, title, summary placeholder, message count, latest preview, and timestamps. Snapshots keep an existing conversation stable when the original character or persona changes.

### `messages`

Each message is a separate document containing its conversation reference, role, content, status, and timestamp.

Messages intentionally remain separate instead of becoming one large array inside a conversation. This avoids rewriting a growing MongoDB document and prevents long chats from approaching MongoDB's per-document size limit.

## Prompt assembly

For each response, AIRO assembles:

1. The global role-play behavior contract
2. Character description and speaking style
3. Selected persona and relationship context
4. Stored conversation summary, when present
5. The newest messages that fit the context budget
6. The latest user message

Character and persona information use separate tagged sections so the model is less likely to confuse their roles.

## Streaming and concurrency

Flask forwards Ollama's stream as newline-delimited JSON. The browser appends token chunks without injecting model output as raw HTML.

The Ollama service uses one process-wide generation lock. On a local computer with one GPU, a second generation waits instead of competing for VRAM.

## Uploaded images

Pillow decodes and validates avatar uploads, strips metadata, center-crops them, resizes them to 512 by 512, and writes WebP files with random names. The upload directory is local runtime data and excluded from Git.

## Security boundaries

AIRO includes password hashing, CSRF validation, ownership checks, safe image decoding, output escaping, sanitized Markdown, upload limits, and login/generation rate limiting.

These controls do not make AIRO ready for untrusted public hosting. A public deployment would require TLS, proxy hardening, secure cookie changes, monitoring, stronger account recovery, and a broader security review.
