from datetime import datetime, timezone

from bson import ObjectId
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .db import get_db, unique_conversations
from .services.avatars import AvatarError, delete_avatar, save_avatar


main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))


@main_bp.get("/favicon.ico")
def favicon():
    return current_app.send_static_file("favicon.svg")


@main_bp.get("/app")
@login_required
def dashboard():
    owner_id = ObjectId(current_user.id)
    characters = list(get_db().characters.find({"owner_id": owner_id}).sort("updated_at", -1))
    conversations = unique_conversations(list(
        get_db().conversations.find({"owner_id": owner_id}).sort("updated_at", -1).limit(30)
    ))[:8]
    character_map = {
        item["_id"]: item for item in get_db().characters.find({"owner_id": owner_id})
    }
    return render_template(
        "dashboard.html",
        characters=characters,
        conversations=conversations,
        character_map=character_map,
    )


@main_bp.route("/settings/profile", methods=["GET", "POST"])
@login_required
def profile_settings():
    db = get_db()
    user_id = ObjectId(current_user.id)
    document = db.users.find_one({"_id": user_id})
    if request.method == "POST":
        display_name = request.form.get("display_name", "").strip()
        if not display_name or len(display_name) > 40:
            flash("Der Anzeigename muss zwischen 1 und 40 Zeichen lang sein.", "error")
            return render_template("settings/profile.html", profile=document)
        update = {"display_name": display_name, "updated_at": datetime.now(timezone.utc)}
        upload = request.files.get("avatar")
        try:
            new_avatar = save_avatar(upload, "user")
        except AvatarError as exc:
            flash(str(exc), "error")
            return render_template("settings/profile.html", profile=document)
        if new_avatar:
            update["avatar"] = new_avatar
            delete_avatar(document.get("avatar"))
        db.users.update_one({"_id": user_id}, {"$set": update})
        flash("Profil gespeichert.", "success")
        return redirect(url_for("main.profile_settings"))
    return render_template("settings/profile.html", profile=document)
