import json
from datetime import datetime, timezone

from bson import ObjectId
from flask import Blueprint, Response, abort, current_app, jsonify, redirect, render_template, request, stream_with_context, url_for
from flask_login import current_user, login_required

from .db import get_db, object_id
from .extensions import limiter
from .services.ollama_client import OllamaError, status as ollama_status, stream_chat
from .services.prompting import build_messages


chat_bp = Blueprint("chat", __name__)


def owned_conversation(conversation_id):
    oid = object_id(conversation_id)
    if not oid:
        abort(404)
    conversation = get_db().conversations.find_one(
        {"_id": oid, "owner_id": ObjectId(current_user.id)}
    )
    if not conversation:
        abort(404)
    return conversation


@chat_bp.route("/characters/<character_id>/start", methods=["GET", "POST"])
@login_required
def start_conversation(character_id):
    db = get_db()
    character_oid = object_id(character_id)
    character = db.characters.find_one(
        {"_id": character_oid, "owner_id": ObjectId(current_user.id)}
    ) if character_oid else None
    if not character:
        abort(404)
    personas = list(db.personas.find({"owner_id": ObjectId(current_user.id)}).sort("updated_at", -1))
    if request.method == "POST":
        persona = None
        persona_id = object_id(request.form.get("persona_id"))
        if persona_id:
            persona = db.personas.find_one(
                {"_id": persona_id, "owner_id": ObjectId(current_user.id)}
            )
            if not persona:
                abort(404)
        existing = db.conversations.find_one(
            {
                "owner_id": ObjectId(current_user.id),
                "character_id": character["_id"],
                "persona_id": persona["_id"] if persona else None,
            },
            sort=[("updated_at", -1)],
        )
        if existing:
            return redirect(url_for("chat.conversation", conversation_id=existing["_id"]))
        now = datetime.now(timezone.utc)
        conversation = {
            "owner_id": ObjectId(current_user.id),
            "character_id": character["_id"],
            "persona_id": persona["_id"] if persona else None,
            "character_snapshot": {key: value for key, value in character.items() if key not in {"owner_id"}},
            "persona_snapshot": (
                {key: value for key, value in persona.items() if key not in {"owner_id"}}
                if persona else None
            ),
            "title": character["name"],
            "summary": "",
            "message_count": 1,
            "last_message_preview": character["greeting"][:180],
            "created_at": now,
            "updated_at": now,
        }
        result = db.conversations.insert_one(conversation)
        db.messages.insert_one({
            "conversation_id": result.inserted_id,
            "role": "assistant",
            "content": character["greeting"],
            "status": "complete",
            "created_at": now,
        })
        return redirect(url_for("chat.conversation", conversation_id=result.inserted_id))
    return render_template("chat/start.html", character=character, personas=personas)


@chat_bp.get("/chat/<conversation_id>")
@login_required
def conversation(conversation_id):
    conversation = owned_conversation(conversation_id)
    messages = list(get_db().messages.find({"conversation_id": conversation["_id"]}).sort("created_at", 1))
    return render_template(
        "chat/conversation.html",
        conversation=conversation,
        character=conversation["character_snapshot"],
        persona=conversation.get("persona_snapshot"),
        messages=messages,
    )


@chat_bp.post("/chat/<conversation_id>/delete")
@login_required
def delete_conversation(conversation_id):
    conversation = owned_conversation(conversation_id)
    db = get_db()
    db.messages.delete_many({"conversation_id": conversation["_id"]})
    db.conversations.delete_one({"_id": conversation["_id"]})
    return redirect(url_for("main.dashboard"))


@chat_bp.get("/api/ollama/status")
@login_required
def model_status():
    return jsonify(ollama_status(current_app.config["OLLAMA_BASE_URL"], current_app.config["OLLAMA_MODEL"]))


@chat_bp.post("/api/conversations/<conversation_id>/messages")
@login_required
@limiter.limit("30 per minute")
def send_message(conversation_id):
    conversation = owned_conversation(conversation_id)
    payload = request.get_json(silent=True) or {}
    content = str(payload.get("content", "")).strip()
    if not content:
        return jsonify({"error": "Die Nachricht ist leer."}), 400
    if len(content) > 12000:
        return jsonify({"error": "Die Nachricht ist zu lang."}), 400

    db = get_db()
    now = datetime.now(timezone.utc)
    db.messages.insert_one({
        "conversation_id": conversation["_id"],
        "role": "user",
        "content": content,
        "status": "complete",
        "created_at": now,
    })
    db.conversations.update_one(
        {"_id": conversation["_id"]},
        {
            "$set": {"updated_at": now, "last_message_preview": content[:180]},
            "$inc": {"message_count": 1},
        },
    )

    history = list(db.messages.find({"conversation_id": conversation["_id"]}).sort("created_at", 1))
    messages = build_messages(
        conversation["character_snapshot"],
        conversation.get("persona_snapshot"),
        conversation,
        history,
    )
    base_url = current_app.config["OLLAMA_BASE_URL"]
    model = current_app.config["OLLAMA_MODEL"]
    conversation_oid = conversation["_id"]

    @stream_with_context
    def generate():
        chunks = []
        status_value = "complete"
        try:
            yield json.dumps({"type": "start"}) + "\n"
            for token in stream_chat(base_url, model, messages):
                chunks.append(token)
                yield json.dumps({"type": "token", "content": token}, ensure_ascii=False) + "\n"
        except GeneratorExit:
            status_value = "interrupted"
            raise
        except OllamaError as exc:
            status_value = "error"
            yield json.dumps({"type": "error", "message": str(exc)}, ensure_ascii=False) + "\n"
        finally:
            if chunks:
                assistant_content = "".join(chunks)
                db.messages.insert_one({
                    "conversation_id": conversation_oid,
                    "role": "assistant",
                    "content": assistant_content,
                    "status": status_value,
                    "created_at": datetime.now(timezone.utc),
                })
                db.conversations.update_one(
                    {"_id": conversation_oid},
                    {
                        "$set": {
                            "updated_at": datetime.now(timezone.utc),
                            "last_message_preview": assistant_content[:180],
                        },
                        "$inc": {"message_count": 1},
                    },
                )
            if status_value == "complete":
                yield json.dumps({"type": "done"}) + "\n"

    return Response(generate(), mimetype="application/x-ndjson")
