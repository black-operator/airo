from app.services.prompting import build_messages, build_system_prompt


def test_prompt_keeps_character_and_persona_separate():
    character = {
        "name": "Mara",
        "tagline": "A quiet archivist",
        "personality": "Observant and dry-witted",
        "speaking_style": "Short, precise sentences",
        "scenario": "An old library",
        "examples": "",
        "instructions": "",
        "reply_length": "balanced",
    }
    persona = {
        "name": "Noah",
        "pronouns": "he/him",
        "appearance": "",
        "personality": "curious",
        "background": "new researcher",
        "relationship": "Mara's assistant",
        "instructions": "",
    }
    prompt = build_system_prompt(character, persona, {"summary": "They found a sealed letter."})
    assert "Your role is the character named Mara" in prompt
    assert "persona named Noah" in prompt
    assert "Never write the user's dialogue" in prompt
    assert "They found a sealed letter" in prompt


def test_history_is_trimmed_from_the_oldest_message():
    character = {"name": "Mara", "reply_length": "balanced"}
    history = [
        {"role": "user", "content": "old" * 8000},
        {"role": "assistant", "content": "recent answer"},
        {"role": "user", "content": "latest question"},
    ]
    messages = build_messages(character, None, {}, history)
    assert messages[-1]["content"] == "latest question"
    assert messages[-2]["content"] == "recent answer"
    assert all(message["content"] != "old" * 8000 for message in messages[1:])
