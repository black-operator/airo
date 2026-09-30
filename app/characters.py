from datetime import datetime, timezone

from bson import ObjectId
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .db import get_db, object_id
from .services.avatars import AvatarError, delete_avatar, save_avatar


characters_bp = Blueprint("characters", __name__, url_prefix="/characters")


def owned_character(character_id):
    oid = object_id(character_id)
    if not oid:
        abort(404)
    document = get_db().characters.find_one(
        {"_id": oid, "owner_id": ObjectId(current_user.id)}
    )
    if not document:
        abort(404)
    return document


def character_payload(existing=None):
    name = request.form.get("name", "").strip()
    greeting = request.form.get("greeting", "").strip()
    if not name:
        raise ValueError("Der Charakter braucht einen Namen.")
    if not greeting:
        raise ValueError("Schreibe eine erste Nachricht für den Charakter.")
    now = datetime.now(timezone.utc)
    payload = {
        "name": name[:60],
        "tagline": request.form.get("tagline", "").strip()[:160],
        "greeting": greeting[:5000],
        "personality": request.form.get("personality", "").strip()[:8000],
        "speaking_style": request.form.get("speaking_style", "").strip()[:4000],
        "scenario": request.form.get("scenario", "").strip()[:8000],
        "examples": request.form.get("examples", "").strip()[:10000],
        "instructions": request.form.get("instructions", "").strip()[:6000],
        "reply_length": request.form.get("reply_length", "balanced"),
        "updated_at": now,
    }
    upload = request.files.get("avatar")
    avatar = save_avatar(upload, "character")
    if avatar:
        payload["avatar"] = avatar
    elif existing and existing.get("avatar"):
        payload["avatar"] = existing["avatar"]
    return payload, avatar


@characters_bp.get("")
@login_required
def list_characters():
    characters = list(
        get_db().characters.find({"owner_id": ObjectId(current_user.id)}).sort("updated_at", -1)
    )
    return render_template("characters/list.html", characters=characters)


@characters_bp.route("/new", methods=["GET", "POST"])
@login_required
def create_character():
    if request.method == "POST":
        try:
            payload, _avatar = character_payload()
            payload.update(
                owner_id=ObjectId(current_user.id),
                created_at=datetime.now(timezone.utc),
            )
            result = get_db().characters.insert_one(payload)
            flash(f"{payload['name']} wurde erstellt.", "success")
            return redirect(url_for("characters.edit_character", character_id=result.inserted_id))
        except (ValueError, AvatarError) as exc:
            flash(str(exc), "error")
    return render_template("characters/form.html", character=None)


@characters_bp.route("/<character_id>/edit", methods=["GET", "POST"])
@login_required
def edit_character(character_id):
    character = owned_character(character_id)
    if request.method == "POST":
        try:
            payload, new_avatar = character_payload(character)
            get_db().characters.update_one({"_id": character["_id"]}, {"$set": payload})
            if new_avatar:
                delete_avatar(character.get("avatar"))
            flash("Charakter gespeichert.", "success")
            return redirect(url_for("characters.edit_character", character_id=character_id))
        except (ValueError, AvatarError) as exc:
            flash(str(exc), "error")
    return render_template("characters/form.html", character=character)


@characters_bp.post("/<character_id>/delete")
@login_required
def delete_character(character_id):
    character = owned_character(character_id)
    db = get_db()
    conversation_ids = [
        item["_id"]
        for item in db.conversations.find(
            {"owner_id": ObjectId(current_user.id), "character_id": character["_id"]}, {"_id": 1}
        )
    ]
    if conversation_ids:
        db.messages.delete_many({"conversation_id": {"$in": conversation_ids}})
        db.conversations.delete_many({"_id": {"$in": conversation_ids}})
    db.characters.delete_one({"_id": character["_id"]})
    delete_avatar(character.get("avatar"))
    flash("Charakter und zugehörige Chats wurden gelöscht.", "success")
    return redirect(url_for("characters.list_characters"))
