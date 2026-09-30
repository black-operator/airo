from bson import ObjectId
from flask import current_app
from pymongo import ASCENDING, DESCENDING


def get_db():
    return current_app.extensions["mongo_db"]


def object_id(value):
    try:
        return ObjectId(str(value))
    except Exception:
        return None


def unique_conversations(conversations):
    """Keep only the newest chat for each character/persona pair without deleting data."""
    seen = set()
    unique = []
    for conversation in conversations:
        key = (conversation.get("character_id"), conversation.get("persona_id"))
        if key in seen:
            continue
        seen.add(key)
        unique.append(conversation)
    return unique


def ensure_indexes(db):
    db.users.create_index([("username_normalized", ASCENDING)], unique=True)
    db.users.create_index([("email_normalized", ASCENDING)], unique=True, sparse=True)
    db.characters.create_index([("owner_id", ASCENDING), ("updated_at", DESCENDING)])
    db.personas.create_index([("owner_id", ASCENDING), ("updated_at", DESCENDING)])
    db.conversations.create_index([("owner_id", ASCENDING), ("updated_at", DESCENDING)])
    db.messages.create_index([("conversation_id", ASCENDING), ("created_at", ASCENDING)])
