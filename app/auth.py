import re
from datetime import datetime, timezone

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from bson import ObjectId
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import UserMixin, current_user, login_user, logout_user
from pymongo.errors import DuplicateKeyError

from .db import get_db, object_id
from .extensions import limiter


auth_bp = Blueprint("auth", __name__)
password_hasher = PasswordHasher()
USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,24}$")


class User(UserMixin):
    def __init__(self, document):
        self.document = document
        self.id = str(document["_id"])
        self.username = document["username"]
        self.display_name = document.get("display_name") or self.username
        self.avatar = document.get("avatar")

    @classmethod
    def get(cls, user_id):
        oid = object_id(user_id)
        if not oid:
            return None
        document = get_db().users.find_one({"_id": oid})
        return cls(document) if document else None


@auth_bp.route("/signup", methods=["GET", "POST"])
@limiter.limit("8 per minute", methods=["POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        display_name = request.form.get("display_name", "").strip() or username
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        errors = []
        if not USERNAME_RE.fullmatch(username):
            errors.append("Der Benutzername braucht 3–24 Zeichen und darf nur Buchstaben, Zahlen und _ enthalten.")
        if len(display_name) > 40:
            errors.append("Der Anzeigename darf höchstens 40 Zeichen lang sein.")
        if len(password) < 8:
            errors.append("Das Passwort muss mindestens 8 Zeichen lang sein.")
        if password != confirm:
            errors.append("Die Passwörter stimmen nicht überein.")

        if not errors:
            now = datetime.now(timezone.utc)
            document = {
                "username": username,
                "username_normalized": username.casefold(),
                "display_name": display_name,
                "password_hash": password_hasher.hash(password),
                "created_at": now,
                "updated_at": now,
            }
            try:
                result = get_db().users.insert_one(document)
                document["_id"] = result.inserted_id
                login_user(User(document), remember=True)
                return redirect(url_for("main.dashboard"))
            except DuplicateKeyError:
                errors.append("Dieser Benutzername ist bereits vergeben.")

        for error in errors:
            flash(error, "error")
    return render_template("auth/signup.html")


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip().casefold()
        password = request.form.get("password", "")
        document = get_db().users.find_one({"username_normalized": username})
        valid = False
        if document:
            try:
                valid = password_hasher.verify(document["password_hash"], password)
            except VerifyMismatchError:
                valid = False
        if valid:
            login_user(User(document), remember=True)
            next_url = request.args.get("next")
            if next_url and next_url.startswith("/") and not next_url.startswith("//"):
                return redirect(next_url)
            return redirect(url_for("main.dashboard"))
        flash("Benutzername oder Passwort ist nicht korrekt.", "error")
    return render_template("auth/login.html")


@auth_bp.post("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
