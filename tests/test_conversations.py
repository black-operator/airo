from bson import ObjectId

from app.db import unique_conversations


def test_unique_conversations_keeps_newest_pair_only():
    character = ObjectId()
    persona = ObjectId()
    newest = {"_id": ObjectId(), "character_id": character, "persona_id": persona}
    duplicate = {"_id": ObjectId(), "character_id": character, "persona_id": persona}
    another = {"_id": ObjectId(), "character_id": character, "persona_id": None}

    assert unique_conversations([newest, duplicate, another]) == [newest, another]
