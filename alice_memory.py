"""Atom memory for an Alice session.

Atoms are notes the person asked to keep. They are not a truth shelf.
A stack card or a tool result still wins a factual question.
"""

from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

KINDS = ("rule", "goal", "preference", "fact", "insight")
STOP = {
    "a", "an", "the", "of", "and", "or", "to", "in", "on", "for", "is", "it",
    "what", "do", "you", "i", "me", "my", "remember", "about", "that", "this",
}


def tokenize(text: str) -> List[str]:
    return [
        tok
        for tok in re.findall(r"[a-z0-9]+", text.lower())
        if len(tok) > 1 and tok not in STOP
    ]


class MemoryStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._con = sqlite3.connect(str(self.path))
        self._con.row_factory = sqlite3.Row
        self._con.execute(
            """
            CREATE TABLE IF NOT EXISTS atoms (
                id INTEGER PRIMARY KEY,
                kind TEXT NOT NULL,
                text TEXT NOT NULL,
                personality TEXT NOT NULL,
                created TEXT NOT NULL
            )
            """
        )
        self._con.commit()

    def close(self) -> None:
        self._con.close()

    def add(self, text: str, kind: str = "fact", personality: str = "chat") -> dict:
        clean = text.strip()
        if not clean:
            raise ValueError("empty memory")
        if kind not in KINDS:
            raise ValueError(f"kind must be one of {', '.join(KINDS)}")
        created = datetime.now(timezone.utc).isoformat()
        cur = self._con.execute(
            "INSERT INTO atoms (kind, text, personality, created) VALUES (?, ?, ?, ?)",
            (kind, clean, personality, created),
        )
        self._con.commit()
        return {"id": int(cur.lastrowid), "kind": kind, "text": clean, "personality": personality}

    def forget(self, needle: str) -> int:
        needle = needle.strip().lower()
        if not needle:
            return 0
        rows = self._con.execute("SELECT id, text FROM atoms").fetchall()
        ids = [int(row["id"]) for row in rows if needle in row["text"].lower()]
        for atom_id in ids:
            self._con.execute("DELETE FROM atoms WHERE id = ?", (atom_id,))
        self._con.commit()
        return len(ids)

    def search(self, query: str, budget_chars: int = 1000, limit: int = 8) -> List[dict]:
        rows = self._con.execute(
            "SELECT id, kind, text, personality, created FROM atoms ORDER BY id"
        ).fetchall()
        terms = tokenize(query)
        ranked = []
        for row in rows:
            text_terms = set(tokenize(row["text"]))
            if row["kind"] == "rule":
                score = 100
            elif not terms:
                score = 1
            else:
                score = len(text_terms.intersection(terms))
            if score <= 0:
                continue
            ranked.append((score, int(row["id"]), dict(row)))
        ranked.sort(key=lambda item: (-item[0], -item[1]))
        chosen: List[dict] = []
        used = 0
        for _score, _atom_id, atom in ranked:
            if len(chosen) >= limit:
                break
            weight = len(atom["text"]) + 24
            if chosen and used + weight > budget_chars:
                continue
            chosen.append(atom)
            used += weight
        rules = [atom for atom in chosen if atom["kind"] == "rule"]
        rest = [atom for atom in chosen if atom["kind"] != "rule"]
        return rules + rest

    def all_atoms(self) -> Iterable[dict]:
        rows = self._con.execute(
            "SELECT id, kind, text, personality, created FROM atoms ORDER BY id"
        ).fetchall()
        return [dict(row) for row in rows]
