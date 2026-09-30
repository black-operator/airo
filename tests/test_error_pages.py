from types import SimpleNamespace

from bson import ObjectId

from app import create_app


def test_favicon_is_served_directly():
    app = create_app({"TESTING": True})
    response = app.test_client().get("/favicon.ico")
    assert response.status_code == 200
    assert response.mimetype == "image/svg+xml"


def test_base_template_owns_its_avatar_macro():
    app = create_app({"TESTING": True})
    character_id = ObjectId()
    conversation_id = ObjectId()
    user = SimpleNamespace(
        is_authenticated=True,
        display_name="Test User",
        username="test-user",
        avatar=None,
    )
    conversation = {
        "_id": conversation_id,
        "title": "Test Chat",
        "character_id": character_id,
        "persona_snapshot": None,
        "character_snapshot": {"_id": character_id, "name": "Mika", "avatar": None},
    }

    with app.test_request_context("/missing"):
        template = app.jinja_env.get_template("error.html")
        rendered = template.render(
            code=404,
            message="Missing",
            current_user=user,
            sidebar_conversations=[conversation],
            csrf_token=lambda: "test-token",
        )

    assert "Test Chat" in rendered
    assert "Missing" in rendered
