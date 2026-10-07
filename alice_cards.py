"""Stack cards compiled from EasyLM FACTS.md, plus feature cards for the two shells."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent
CARDS_PATH = ROOT / "stacks_cards.jsonl"

STOP = {
    "a", "an", "the", "of", "and", "or", "to", "in", "on", "for", "is", "it",
    "what", "whats", "does", "how", "why", "with", "from", "this", "that",
    "are", "be", "about", "which", "explain", "show", "tell", "me", "find",
    "please", "define", "who", "describe",
}

FEATURES: List[Dict[str, str]] = [
    {
        "card_id": "feature:stacks",
        "kind": "feature",
        "topic": "stacks",
        "comment": (
            "The stacks are the offline undergraduate shelves. Ask for a subject "
            "or a named fact. A hit returns the stored sentence, its Dewey code, and the door."
        ),
        "cues": "stacks library shelf shelves textbook fact",
    },
    {
        "card_id": "feature:hands",
        "kind": "feature",
        "topic": "hands",
        "comment": (
            "Local hands are calc, units, datetime, stacks, and memory. "
            "They run before any model sample. A pinned card does not open a socket."
        ),
        "cues": "hands hand tools calc units datetime convert clock",
    },
    {
        "card_id": "feature:memory",
        "kind": "feature",
        "topic": "memory",
        "comment": (
            "Memory stores a note you asked to keep: rule, goal, preference, fact, or insight. "
            "Say 'remember preference: ...' or 'what do you remember'. A memory note is not a source for a new fact."
        ),
        "cues": "memory remember atom atmem note",
    },
    {
        "card_id": "feature:personalities",
        "kind": "feature",
        "topic": "personalities",
        "comment": (
            "Voices are coder, researcher, free chat, and creative writer. "
            "A voice changes tone. The receipt still names the shelf."
        ),
        "cues": "personality personalities voice coder researcher writer chat",
    },
    {
        "card_id": "feature:studio",
        "kind": "feature",
        "topic": "studio",
        "comment": (
            "EasyLM Studio reads markdown, writes notes, edits code, graphs a function, and draws. "
            "It stays on the device."
        ),
        "cues": "studio read write code graph draw canvas",
    },
    {
        "card_id": "feature:hydra",
        "kind": "feature",
        "topic": "hydra",
        "comment": (
            "Hydra commands: hands for a local answer, agent for a tool loop, free for one repair completion, "
            "swarm for the heads, serve for the local OpenAI gateway, mcp for community servers."
        ),
        "cues": "hydra agent swarm serve mcp free forge",
    },
    {
        "card_id": "feature:alice",
        "kind": "feature",
        "topic": "alice",
        "comment": (
            "Alice answers from a stack card, a feature card, or a typed tool. "
            "If those miss, she names the gap. A model sample is a sample, not the ground."
        ),
        "cues": "alice emap route abstain receipt",
    },
]


def tokenize(text: str) -> List[str]:
    return [
        tok
        for tok in re.findall(r"[a-z0-9]+", text.lower())
        if len(tok) > 1 and tok not in STOP
    ]


def strip_ask(text: str) -> str:
    cleaned = text.strip().rstrip("?.!")
    cleaned = re.sub(
        r"^(?:please\s+)?(?:what(?:'s| is)|define|explain|tell me about|who is|describe)\s+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    return cleaned.strip()


@lru_cache(maxsize=1)
def load_stack_cards(path: str = "") -> tuple:
    source = Path(path) if path else CARDS_PATH
    if not source.exists():
        return tuple()
    cards = []
    for line in source.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            cards.append(json.loads(line))
    return tuple(cards)


def search_stacks(query: str, cards_path: Optional[Path] = None, limit: int = 3) -> List[dict]:
    raw = strip_ask(query).lower()
    terms = tokenize(raw)
    if len(terms) < 2:
        return []
    cards = load_stack_cards(str(cards_path) if cards_path else "")
    hits = []
    for card in cards:
        topic = card["topic"].lower()
        topic_terms = tokenize(card["topic"])
        if raw and raw in topic:
            score = 100 + len(terms)
        elif all(term in topic_terms or term in topic for term in terms):
            score = 40 + len(terms)
        else:
            continue
        hits.append((score, card))
    hits.sort(key=lambda item: (-item[0], item[1]["topic"]))
    return [card for _score, card in hits[:limit]]


def search_features(query: str) -> Optional[dict]:
    if not re.search(r"\b(how|help|what can you|how do i|how to)\b", query, flags=re.IGNORECASE):
        return None
    terms = set(tokenize(query))
    best = None
    best_score = 0
    for feature in FEATURES:
        cues = set(feature["cues"].split())
        score = len(terms.intersection(cues))
        if score > best_score:
            best = feature
            best_score = score
    if best_score <= 0:
        return None
    return best
