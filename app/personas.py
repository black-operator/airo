from datetime import datetime, timezone

from bson import ObjectId
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .db import get_db, object_id
from .services.avatars import AvatarError, delete_avatar, save_avatar


personas_bp = Blueprint("personas", __name__, url_prefix="/personas")


def owned_persona(persona_id):
    oid = object_id(persona_id)
    if not oid:
        abort(404)
    persona = get_db().personas.find_one({"_id": oid, "owner_id": ObjectId(current_user.id)})
    if not persona:
        abort(404)
    return persona


def persona_payload(existing=None):
    name = request.form.get("name", "").strip()
    if not name:
        raise ValueError("Die Persona braucht einen Namen.")
    payload = {
        "name": name[:60],
        "pronouns": request.form.get("pronouns", "").strip()[:80],
        "appearance": request.form.get("appearance", "").strip()[:4000],
        "personality": request.form.get("personality", "").strip()[:5000],
        "background": request.form.get("background", "").strip()[:6000],
        "relationship": request.form.get("relationship", "").strip()[:4000],
        "instructions": request.form.get("instructions", "").strip()[:5000],
        "updated_at": datetime.now(timezone.utc),
    }
    avatar = save_avatar(request.files.get("avatar"), "persona")
    if avatar:
        payload["avatar"] = avatar
    elif existing and existing.get("avatar"):
        payload["avatar"] = existing["avatar"]
    return payload, avatar


@personas_bp.get("")
@login_required
def list_personas():
    personas = list(
        get_db().personas.find({"owner_id": ObjectId(current_user.id)}).sort("updated_at", -1)
    )
    return render_template("personas/list.html", personas=personas)


@personas_bp.route("/new", methods=["GET", "POST"])
@login_required
def create_persona():
    if request.method == "POST":
        try:
            payload, _avatar = persona_payload()
            payload.update(owner_id=ObjectId(current_user.id), created_at=datetime.now(timezone.utc))
            result = get_db().personas.insert_one(payload)
            flash(f"Persona {payload['name']} wurde erstellt.", "success")
            return redirect(url_for("personas.edit_persona", persona_id=result.inserted_id))
        except (ValueError, AvatarError) as exc:
            flash(str(exc), "error")
    return render_template("personas/form.html", persona=None)


@personas_bp.route("/<persona_id>/edit", methods=["GET", "POST"])
@login_required
def edit_persona(persona_id):
    persona = owned_persona(persona_id)
    if request.method == "POST":
        try:
            payload, new_avatar = persona_payload(persona)
            get_db().personas.update_one({"_id": persona["_id"]}, {"$set": payload})
            if new_avatar:
                delete_avatar(persona.get("avatar"))
            flash("Persona gespeichert.", "success")
            return redirect(url_for("personas.edit_persona", persona_id=persona_id))
        except (ValueError, AvatarError) as exc:
            flash(str(exc), "error")
    return render_template("personas/form.html", persona=persona)


@personas_bp.post("/<persona_id>/delete")
@login_required
def delete_persona(persona_id):
    persona = owned_persona(persona_id)
    get_db().personas.delete_one({"_id": persona["_id"]})
    delete_avatar(persona.get("avatar"))
    flash("Persona gelöscht. Bestehende Chats behalten ihren Snapshot.", "success")
    return redirect(url_for("personas.list_personas"))
