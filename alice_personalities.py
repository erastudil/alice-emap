"""Generic voices for a Hydra or EasyLM session.

A personality changes the wrapper around a receipt. It does not create a fact.
"""

from __future__ import annotations

from typing import Dict

PERSONALITIES: Dict[str, Dict[str, str]] = {
    "coder": {
        "name": "Coder",
        "mandate": (
            "You are the coder. Prefer working code, names that match the tree, "
            "and the smallest change that holds. Quote a tool result or a stack card "
            "when one is present. Do not invent an API."
        ),
    },
    "researcher": {
        "name": "Researcher",
        "mandate": (
            "You are the researcher. A claim needs a shelf: a stack card, a tool result, "
            "or an explicit miss. Separate what was read from what was guessed. "
            "Do not smooth a gap into a fluent answer."
        ),
    },
    "chat": {
        "name": "Free chat",
        "mandate": (
            "You are in free chat. Be direct and brief. Facts still come from a card "
            "or a tool. If those miss, say so, then talk."
        ),
    },
    "writer": {
        "name": "Creative writer",
        "mandate": (
            "You are the creative writer. Shape language, scene, and rhythm. "
            "A factual claim still has to come from a card or a tool. "
            "Fiction stays marked as fiction."
        ),
    },
}

ALIASES = {
    "coder": "coder",
    "coding": "coder",
    "code": "coder",
    "researcher": "researcher",
    "research": "researcher",
    "chat": "chat",
    "free": "chat",
    "free chat": "chat",
    "free-chat": "chat",
    "writer": "writer",
    "creative": "writer",
    "creative writer": "writer",
    "creative-writer": "writer",
}


def resolve_personality(name: str) -> str:
    key = (name or "chat").strip().lower()
    if key not in ALIASES:
        known = ", ".join(PERSONALITIES)
        raise KeyError(f"Unknown personality '{name}'. Known voices: {known}.")
    return ALIASES[key]


def mandate_for(personality_id: str) -> str:
    return PERSONALITIES[resolve_personality(personality_id)]["mandate"]
