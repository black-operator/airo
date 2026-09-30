from pathlib import Path

import bleach
import markdown
from flask import Flask, render_template
from flask_login import current_user
from markupsafe import Markup
from bson import ObjectId
from pymongo import MongoClient

from .config import Config
from .db import ensure_indexes, unique_conversations
from .extensions import csrf, limiter, login_manager


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    mongo_client = MongoClient(
        app.config["MONGO_URI"],
        serverSelectionTimeoutMS=2500,
        connectTimeoutMS=2500,
    )
    mongo_db = mongo_client[app.config["MONGO_DB"]]
    app.extensions["mongo_client"] = mongo_client
    app.extensions["mongo_db"] = mongo_db

    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    from .auth import User, auth_bp
    from .characters import characters_bp
    from .chat import chat_bp
    from .main import main_bp
    from .personas import personas_bp

    @login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(characters_bp)
    app.register_blueprint(personas_bp)
    app.register_blueprint(chat_bp)

    @app.template_filter("chat_markdown")
    def chat_markdown(value):
        rendered = markdown.markdown(
            value or "",
            extensions=[],
            output_format="html",
        )
        cleaned = bleach.clean(
            rendered,
            tags={"p", "br", "em", "strong"},
            attributes={},
            strip=True,
        )
        return Markup(cleaned)

    @app.context_processor
    def sidebar_context():
        if not current_user.is_authenticated:
            return {"sidebar_conversations": []}
        conversations = unique_conversations(list(
            mongo_db.conversations.find({"owner_id": ObjectId(current_user.id)})
            .sort("updated_at", -1)
            .limit(40)
        ))[:12]
        return {"sidebar_conversations": conversations}

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("error.html", code=404, message="Diese Seite existiert nicht."), 404

    @app.errorhandler(413)
    def too_large(_error):
        return render_template("error.html", code=413, message="Die Datei ist zu groß."), 413

    with app.app_context():
        try:
            mongo_client.admin.command("ping")
            ensure_indexes(mongo_db)
        except Exception as exc:
            app.logger.warning("MongoDB ist noch nicht erreichbar: %s", exc)

    return app
