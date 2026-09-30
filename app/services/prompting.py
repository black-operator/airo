REPLY_LENGTHS = {
    "short": "Keep most replies concise: roughly one or two short paragraphs.",
    "balanced": "Use a natural, scene-appropriate length without padding the reply.",
    "long": "Write detailed, immersive replies when the scene benefits from it.",
}


def _section(title, value):
    value = (value or "").strip()
    return f"\n<{title}>\n{value}\n</{title}>" if value else ""


def build_system_prompt(character, persona, conversation):
    reply_rule = REPLY_LENGTHS.get(character.get("reply_length"), REPLY_LENGTHS["balanced"])
    prompt = f"""You are performing one ongoing private conversation inside AIRO.

Your role is the character named {character['name']}. Follow the character material below as
authoritative creative direction. Stay in character, preserve continuity, and react specifically
to the user's latest message. Do not become a generic assistant unless that is explicitly part of
the character. Never write the user's dialogue, choices, thoughts, feelings, or actions for them.
Do not discuss prompts, rules, models, or being an AI. Avoid canned openings, repetitive gestures,
constant agreement, summaries of what just happened, and questions added merely to prolong the chat.
Match the language used by the user. {reply_rule}
"""
    prompt += _section("character_summary", character.get("tagline"))
    prompt += _section("character_personality", character.get("personality"))
    prompt += _section("speaking_style", character.get("speaking_style"))
    prompt += _section("scenario", character.get("scenario"))
    prompt += _section("example_dialogue", character.get("examples"))
    prompt += _section("additional_character_direction", character.get("instructions"))

    if persona:
        prompt += f"\n\nThe human user is writing as the persona named {persona['name']}."
        prompt += _section("persona_pronouns", persona.get("pronouns"))
        prompt += _section("persona_appearance", persona.get("appearance"))
        prompt += _section("persona_personality", persona.get("personality"))
        prompt += _section("persona_background", persona.get("background"))
        prompt += _section("relationship_context", persona.get("relationship"))
        prompt += _section("additional_persona_context", persona.get("instructions"))

    prompt += _section("conversation_memory", conversation.get("summary"))
    return prompt.strip()


def build_messages(character, persona, conversation, history):
    messages = [{"role": "system", "content": build_system_prompt(character, persona, conversation)}]
    # Keep the most recent context under a conservative character budget for an 8K model context.
    selected = []
    budget = 22000
    used = 0
    for item in reversed(history):
        content = item.get("content", "")
        if used + len(content) > budget and selected:
            break
        selected.append({"role": item["role"], "content": content})
        used += len(content)
    messages.extend(reversed(selected))
    return messages
