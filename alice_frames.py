"""alice_frames.py - L1 Frame Table & Open Pointer Walk for Alice 1.0 EMap.

Implements SPEC.md sections 4 and 5 (L1 frames) and QUEUE.md Q3.1-Q3.3:
- Closed set of 14 L1 frames: define, hypernym, hyponym, part, antonym, synonym,
  cause, dewey, arithmetic, convert, datetime, stack, feature, fresh.
- Open pointer resolution over the walkable subgraph in emap.db:
  exact lemma -> form_of / derivation / pertainym -> synonym -> hypernym,
  recording every hop for the DecisionReceipt metadata.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Set, Tuple

CLOSED_OPERATORS: Set[str] = {
    "what", "whats", "who", "where", "when", "why", "how", "which",
    "is", "are", "was", "were", "do", "does", "did", "can", "could",
    "a", "an", "the", "of", "in", "to", "into", "for", "from", "with", "on", "by",
    "define", "meaning", "definition", "hypernym", "kind", "hyponym", "subtype",
    "part", "parts", "meronym", "antonym", "opposite", "synonym", "similar",
    "cause", "causes", "entails", "dewey", "code", "category", "classification", "shelf",
    "calculate", "compute", "solve", "simplify", "gcd", "lcm", "sqrt",
    "convert", "days", "between", "leap", "year", "week", "day", "utc", "current", "today",
    "use", "help", "feature", "studio", "stacks", "memory", "hands", "hydra",
    "latest", "live", "refresh", "fresh", "nist", "wikipedia",
}


@dataclass
class FrameMatch:
    frame: str
    slot: str
    relation: Optional[str] = None
    target_unit: Optional[str] = None
    extra: Dict[str, str] = field(default_factory=dict)


def _clean(query: str) -> str:
    return query.strip()


def frame_define(query: str) -> Optional[FrameMatch]:
    m = re.match(
        r"^(?:please\s+)?(?:define|meaning\s+of|definition\s+of)\s+([a-zA-Z]+)[?.!]*$",
        _clean(query),
        flags=re.IGNORECASE,
    )
    if m:
        return FrameMatch(frame="define", slot=m.group(1).lower())
    return None


def frame_hypernym(query: str) -> Optional[FrameMatch]:
    m = re.match(
        r"^(?:what\s+is\s+(?:the\s+|a\s+)?)?(?:hypernym|kind)\s+of\s+([a-zA-Z]+)[?.!]*$",
        _clean(query),
        flags=re.IGNORECASE,
    )
    if m:
        return FrameMatch(frame="hypernym", slot=m.group(1).lower(), relation="hypernym")
    return None


def frame_hyponym(query: str) -> Optional[FrameMatch]:
    m = re.match(
        r"^(?:what\s+(?:is|are)\s+(?:the\s+|a\s+)?)?(?:hyponyms?|subtypes?|examples?|specific\s+kinds?)\s+of\s+([a-zA-Z]+)[?.!]*$",
        _clean(query),
        flags=re.IGNORECASE,
    )
    if m:
        return FrameMatch(frame="hyponym", slot=m.group(1).lower(), relation="hyponym")
    return None


def frame_part(query: str) -> Optional[FrameMatch]:
    m = re.match(
        r"^(?:what\s+(?:is|are)\s+(?:the\s+|a\s+)?)?(?:part|parts|meronym)\s+of\s+([a-zA-Z]+)[?.!]*$",
        _clean(query),
        flags=re.IGNORECASE,
    )
    if m:
        return FrameMatch(frame="part", slot=m.group(1).lower(), relation="part")
    return None


def frame_antonym(query: str) -> Optional[FrameMatch]:
    m = re.match(
        r"^(?:what\s+is\s+(?:the\s+)?)?(?:antonym|opposite)\s+of\s+([a-zA-Z]+)[?.!]*$",
        _clean(query),
        flags=re.IGNORECASE,
    )
    if m:
        return FrameMatch(frame="antonym", slot=m.group(1).lower(), relation="antonym")
    return None


def frame_synonym(query: str) -> Optional[FrameMatch]:
    m = re.match(
        r"^(?:what\s+is\s+(?:the\s+|a\s+)?)?(?:synonym|similar\s+word)\s+(?:of|for)\s+([a-zA-Z]+)[?.!]*$",
        _clean(query),
        flags=re.IGNORECASE,
    )
    if m:
        return FrameMatch(frame="synonym", slot=m.group(1).lower(), relation="synonym")
    return None


def frame_cause(query: str) -> Optional[FrameMatch]:
    q = _clean(query)
    m1 = re.match(
        r"^(?:what\s+does\s+)([a-zA-Z]+)\s+(?:cause|entail)[?.!]*$",
        q,
        flags=re.IGNORECASE,
    )
    if m1:
        return FrameMatch(frame="cause", slot=m1.group(1).lower(), relation="causes")
    m2 = re.match(
        r"^(?:what\s+(?:is|are)\s+(?:the\s+)?)?(?:causes?|effects?|entailments?)\s+(?:of\s+)?([a-zA-Z]+)[?.!]*$",
        q,
        flags=re.IGNORECASE,
    )
    if m2:
        return FrameMatch(frame="cause", slot=m2.group(1).lower(), relation="causes")
    return None


def frame_dewey(query: str) -> Optional[FrameMatch]:
    m = re.match(
        r"^(?:what\s+is\s+the\s+)?dewey\s+(?:code|category|classification|shelf)?\s*(?:for|of)?\s+([a-zA-Z]+)[?.!]*$",
        _clean(query),
        flags=re.IGNORECASE,
    )
    if m:
        return FrameMatch(frame="dewey", slot=m.group(1).lower())
    return None


def frame_arithmetic(query: str) -> Optional[FrameMatch]:
    clean = re.sub(
        r"^(?:calculate|compute|solve|simplify|what\s+is)\s+",
        "",
        _clean(query),
        flags=re.IGNORECASE,
    ).rstrip("?=").strip()
    if re.match(r"^(?:gcd|lcm)\s*\(\s*\d+\s*,\s*\d+\s*\)$", clean, flags=re.IGNORECASE):
        return FrameMatch(frame="arithmetic", slot=clean)
    if re.match(r"^sqrt\s*\(\s*\d+\s*\)$", clean, flags=re.IGNORECASE):
        return FrameMatch(frame="arithmetic", slot=clean)
    if re.match(r"^[\d\s\+\-\*\/\(\)\^]+$", clean) and any(op in clean for op in "+-*/^"):
        return FrameMatch(frame="arithmetic", slot=clean)
    return None


def frame_convert(query: str) -> Optional[FrameMatch]:
    q = _clean(query)
    if re.search(r"\bUTC[+-]?\d*\b", q, flags=re.IGNORECASE):
        return None
    m_num = re.search(
        r"(\d+(?:\.\d+)?)\s*([a-zA-Z\/]+)\s+(?:in|to|into)\s+([a-zA-Z\/\s]+?)[?.!]*$",
        q,
        flags=re.IGNORECASE,
    )
    if m_num:
        return FrameMatch(
            frame="convert",
            slot=f"{m_num.group(1)} {m_num.group(2)}",
            target_unit=m_num.group(3).strip(),
        )
    m_named = re.match(
        r"^(?:convert\s+|what\s+is\s+(?:the\s+)?)?([a-zA-Z][a-zA-Z\s]+?)\s+(?:in|to|into)\s+(miles\s+per\s+hour|mph|km\/h|kmh|m\/s|knots?|kilometers?|meters?|miles?|feet|ft|kelvin|celsius|fahrenheit)[?.!]*$",
        q,
        flags=re.IGNORECASE,
    )
    if m_named:
        return FrameMatch(
            frame="convert",
            slot=m_named.group(1).strip().lower(),
            target_unit=m_named.group(2).strip().lower(),
        )
    return None


def frame_datetime(query: str) -> Optional[FrameMatch]:
    q = _clean(query)
    if (
        re.search(r"days\s+between\s+\d{4}-\d{2}-\d{2}\s+and\s+\d{4}-\d{2}-\d{2}", q, re.IGNORECASE)
        or re.search(r"\d{4}-\d{2}-\d{2}\s*[\+\-]\s*\d+\s*days?", q, re.IGNORECASE)
        or re.search(r"convert\s+\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}\s*UTC\s+to\s+UTC[+-]\d+", q, re.IGNORECASE)
        or re.search(r"is\s+\d{1,4}\s+(?:a\s+)?leap\s+year", q, re.IGNORECASE)
        or re.search(r"day\s+of\s+(?:the\s+)?week\s+(?:for|on)\s+\d{4}-\d{2}-\d{2}", q, re.IGNORECASE)
        or re.search(r"\b(current|today'?s)\s+(date|time|timestamp)\b", q, re.IGNORECASE)
    ):
        return FrameMatch(frame="datetime", slot=q)
    m_named = re.match(
        r"^([a-zA-Z][a-zA-Z\s]+?)\s*([\+\-])\s*(\d+)\s*days?[?.!]*$",
        q,
        flags=re.IGNORECASE,
    )
    if m_named:
        return FrameMatch(
            frame="datetime",
            slot=m_named.group(1).strip().lower(),
            extra={"op": m_named.group(2), "days": m_named.group(3)},
        )
    return None


def frame_feature(query: str) -> Optional[FrameMatch]:
    q = _clean(query)
    if re.search(r"\b(how\s+do\s+i|how\s+to|what\s+can\s+you|help\s+with)\b", q, flags=re.IGNORECASE):
        return FrameMatch(frame="feature", slot=q)
    return None


def frame_fresh(query: str) -> Optional[FrameMatch]:
    q = _clean(query)
    m_from = re.search(r"\bfrom\s+([a-z0-9.-]+\.[a-z]{2,})\b", q, flags=re.IGNORECASE)
    if m_from or re.search(r"\b(live|refresh|fresh|latest\s+from)\b", q, flags=re.IGNORECASE):
        domain = m_from.group(1).lower() if m_from else ""
        return FrameMatch(frame="fresh", slot=q, extra={"domain": domain})
    return None


def frame_stack(query: str) -> Optional[FrameMatch]:
    q = _clean(query)
    cleaned = re.sub(
        r"^(?:please\s+)?(?:what(?:'s|\s+is)|explain|tell\s+me\s+about|who\s+is|describe)\s+",
        "",
        q.rstrip("?.!"),
        flags=re.IGNORECASE,
    ).strip()
    tokens = [
        t for t in re.findall(r"[a-z0-9]+", cleaned.lower())
        if len(t) > 1 and t not in CLOSED_OPERATORS
    ]
    if tokens:
        return FrameMatch(frame="stack", slot=cleaned.lower())
    return None


FRAME_TABLE: Dict[str, Callable[[str], Optional[FrameMatch]]] = {
    "define": frame_define,
    "hypernym": frame_hypernym,
    "hyponym": frame_hyponym,
    "part": frame_part,
    "antonym": frame_antonym,
    "synonym": frame_synonym,
    "cause": frame_cause,
    "dewey": frame_dewey,
    "arithmetic": frame_arithmetic,
    "convert": frame_convert,
    "datetime": frame_datetime,
    "feature": frame_feature,
    "fresh": frame_fresh,
    "stack": frame_stack,
}

LEXICON_FRAMES: Tuple[str, ...] = (
    "define",
    "hypernym",
    "hyponym",
    "part",
    "antonym",
    "synonym",
    "cause",
    "dewey",
)


def match_l1_frame(query: str) -> Optional[FrameMatch]:
    """Evaluate the ordered L1 frame table over a query."""
    order = (
        "arithmetic",
        "datetime",
        "convert",
        "define",
        "hypernym",
        "hyponym",
        "part",
        "antonym",
        "synonym",
        "cause",
        "dewey",
        "feature",
        "fresh",
        "stack",
    )
    for name in order:
        matched = FRAME_TABLE[name](query)
        if matched is not None:
            return matched
    return None


def match_lexicon_frame(query: str) -> Optional[FrameMatch]:
    """Evaluate strictly the L0/L1 lexicon frames in front of RETRIEVE."""
    for name in LEXICON_FRAMES:
        matched = FRAME_TABLE[name](query)
        if matched is not None:
            return matched
    return None


def resolve_pointer_hops(conn: sqlite3.Connection, token: str) -> Tuple[Optional[str], List[str]]:
    """Resolve an open pointer token onto a sensed lemma in the walkable subgraph.

    Resolution order (SPEC.md section 4):
    1. Exact lemma in `nodes` (plus any canonical `form_of`, `derivation`, or `pertainym` bridge hop)
    2. One hop along `form_of`, `derivation`, or `pertainym` in walkable `edges`
    3. One `synonym` hop in walkable `edges`
    4. One `hypernym` hop in walkable `edges`
    """
    lem = token.strip().lower()
    if not lem:
        return None, ["ungrounded:empty"]

    cur = conn.cursor()
    cur.execute("SELECT lemma FROM nodes WHERE lemma = ? LIMIT 1", (lem,))
    row = cur.fetchone()
    if row:
        hops = [f"exact:{lem}"]
        for rel in ("form_of", "derivation", "pertainym"):
            cur.execute(
                """
                SELECT e.target_lemma
                FROM edges e
                JOIN nodes n ON n.lemma = e.target_lemma
                WHERE e.source_lemma = ? AND e.relation = ? AND e.target_id IS NOT NULL
                ORDER BY e.weight DESC LIMIT 1
                """,
                (lem, rel),
            )
            r_out = cur.fetchone()
            if r_out:
                hops.append(f"{lem}--{rel}-->{r_out[0]}")
            cur.execute(
                """
                SELECT e.source_lemma
                FROM edges e
                JOIN nodes n ON n.lemma = e.source_lemma
                WHERE e.target_lemma = ? AND e.relation = ? AND e.target_id IS NOT NULL
                ORDER BY e.weight DESC LIMIT 1
                """,
                (lem, rel),
            )
            r_in = cur.fetchone()
            if r_in:
                hops.append(f"{r_in[0]}--{rel}-->{lem}")
        return str(row[0]), hops

    # Step 2: morphological/derivational bridge (form_of, derivation, pertainym)
    for rel in ("form_of", "derivation", "pertainym"):
        cur.execute(
            """
            SELECT e.target_lemma
            FROM edges e
            JOIN nodes n ON n.lemma = e.target_lemma
            WHERE e.source_lemma = ? AND e.relation = ? AND e.target_id IS NOT NULL
            ORDER BY e.weight DESC LIMIT 1
            """,
            (lem, rel),
        )
        r = cur.fetchone()
        if r:
            target = str(r[0])
            return target, [f"{lem}--{rel}-->{target}"]

    # Step 3: one synonym hop
    cur.execute(
        """
        SELECT e.target_lemma
        FROM edges e
        JOIN nodes n ON n.lemma = e.target_lemma
        WHERE e.source_lemma = ? AND e.relation = 'synonym' AND e.target_id IS NOT NULL
        ORDER BY e.weight DESC LIMIT 1
        """,
        (lem,),
    )
    r = cur.fetchone()
    if r:
        target = str(r[0])
        return target, [f"{lem}--synonym-->{target}"]

    # Step 4: one hypernym hop
    cur.execute(
        """
        SELECT e.target_lemma
        FROM edges e
        JOIN nodes n ON n.lemma = e.target_lemma
        WHERE e.source_lemma = ? AND e.relation = 'hypernym' AND e.target_id IS NOT NULL
        ORDER BY e.weight DESC LIMIT 1
        """,
        (lem,),
    )
    r = cur.fetchone()
    if r:
        target = str(r[0])
        return target, [f"{lem}--hypernym-->{target}"]

    return None, [f"ungrounded:{lem}"]
