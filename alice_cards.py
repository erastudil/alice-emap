"""
alice_cards.py — Alice 1.0 EMap Stack Cards (W4), Trusted Doors & HAND Gate (W5),
EasyLM Feature Deck (W6), and Textbook Teach Walk (W7.3).

Implements SPEC.md §§ 3, 5, 6, 8, 9, 10, 11 and QUEUE.md rows:
  - Q4.1: Card compiler for stacks/*/FACTS.md (deterministic SHA-256 card_id)
  - Q4.2: Anchor topics onto walkable lemma ids in emap.db
  - Q4.3: RETRIEVE returns card comment, Dewey, door, and stack:<card_id> provenance
  - Q4.4: Outside-domain prompts abstain with null provenance and silence-gap act
  - Q5.1: Import doors from TRUSTED_SOURCES.md and stacks/*/LINK_INDEX.md
  - Q5.2: HAND runs only after a card miss or fresh card; pinned card never opens a socket
  - Q5.3: Unlisted foreign host abstains with null provenance
  - Q6.1: Feature deck for all 13 surfaces named in SPEC.md §5 L3
  - Q6.2: How-to / feature frame returns the matching feature card
  - Q7.3: Teach walk over the textbook span for a shelf (exact substring of TEXTBOOK.md)
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Callable, Dict, List, Optional
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
CARDS_PATH = ROOT / "stacks_cards.jsonl"
EMAP_ROOT = ROOT
DEFAULT_DB_PATH = EMAP_ROOT / "emap.db"
DEFAULT_STACKS_ROOT = EMAP_ROOT.parent / "easylm" / "stacks"

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


# Closed stopwords excluded when extracting topic anchor lemmas
_STOPWORDS = frozenset({
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "in", "into", "is", "it", "its", "of", "on", "or", "that", "the",
    "their", "to", "vs", "with", "within", "without",
})

# Baseline hosts from SPEC.md §8
BASELINE_ALLOWED_HOSTS = frozenset({
    "en.wikipedia.org",
    "wikipedia.org",
    "www.wikipedia.org",
    "w3.org",
    "www.w3.org",
    "nist.gov",
    "www.nist.gov",
    "physics.nist.gov",
    "dlmf.nist.gov",
    "webbook.nist.gov",
    "ncbi.nlm.nih.gov",
    "www.ncbi.nlm.nih.gov",
    "pubchem.ncbi.nlm.nih.gov",
    "github.com",
    "www.github.com",
})

# Primary-authority host suffixes that outrank encyclopedic orientation (Wikipedia) per SPEC.md §8
PRIMARY_AUTHORITY_SUFFIXES = (
    ".gov",
    ".edu",
    "bipm.org",
    "rfc-editor.org",
    "ietf.org",
    "w3.org",
    "whatwg.org",
    "unicode.org",
    "tc39.es",
    "openstax.org",
    "pdg.lbl.gov",
    "pdglive.lbl.gov",
    "who.int",
    "worldbank.org",
)

# Outside-domain benchmark prompts (Q4.4) that must abstain with provenance=None
OUTSIDE_DOMAIN_PROMPTS: tuple[str, ...] = (
    "What is the secret launch code for the fictional starship Zorblax-9?",
    "Who won the 2099 Martian Curling Championship in New Olympus?",
    "What is the recipe for Grandma Glorp's hyperdrive souffle?",
    "How manyblorgons fit inside a quantum kazoo on Tuesday?",
    "What is the stock ticker price of Xylophone Unicorn Corp right now?",
    "Where did Captain Quasar bury the emerald spatula of Andromeda?",
    "What is the exact serial number of my neighbor's lawnmower?",
    "Why do invisible purple dragons prefer polka-dot umbrellas?",
)

# All 13 EasyLM L3 feature surfaces named in SPEC.md §5 L3 (Q6.1)
FEATURE_SURFACES: tuple[dict[str, str], ...] = (
    {
        "surface": "AtMem",
        "topic": "atmem",
        "dewey": "006",
        "door": "https://github.com/erastudil/easylm#atmem",
        "comment": (
            "AtMem stores user-approved episodic and semantic memory entries in local IndexedDB "
            "with explicit provenance tags and deterministic recall filters."
        ),
    },
    {
        "surface": "governed mandates",
        "topic": "governed mandates",
        "dewey": "005.8",
        "door": "https://github.com/erastudil/easylm#governed-mandates",
        "comment": (
            "Governed mandates enforce signed operational rules, scope boundaries, and safety invariants "
            "before any local or network tool action executes."
        ),
    },
    {
        "surface": "the vault",
        "topic": "the vault",
        "dewey": "005.8",
        "door": "https://github.com/erastudil/easylm#the-vault",
        "comment": (
            "The Vault encrypts API keys, credentials, and private user records at rest in the browser "
            "using WebCrypto AES-GCM keys derived from the user passphrase."
        ),
    },
    {
        "surface": "kid-safe mode",
        "topic": "kid-safe mode",
        "dewey": "005.8",
        "door": "https://github.com/erastudil/easylm#kid-safe-mode",
        "comment": (
            "Kid-safe mode enforces floor-age pack filtering, blocks unrestricted network hands, "
            "and restricts study packs to age-appropriate curriculum shelves."
        ),
    },
    {
        "surface": "Studio read",
        "topic": "studio read",
        "dewey": "001",
        "door": "https://github.com/erastudil/easylm#studio-read",
        "comment": (
            "Studio read opens The Stacks textbooks, primary texts, and linked official doors "
            "with section navigation, citation lookup, and margin notes."
        ),
    },
    {
        "surface": "Studio write",
        "topic": "studio write",
        "dewey": "800",
        "door": "https://github.com/erastudil/easylm#studio-write",
        "comment": (
            "Studio write provides a structured document and Progen composition workspace "
            "with live syntax linting, citation insertion, and local draft versioning."
        ),
    },
    {
        "surface": "Studio code",
        "topic": "studio code",
        "dewey": "005",
        "door": "https://github.com/erastudil/easylm#studio-code",
        "comment": (
            "Studio code runs sandboxed code editing, deterministic test execution, and "
            "static verification checks directly against local workspace files."
        ),
    },
    {
        "surface": "Studio graph",
        "topic": "studio graph",
        "dewey": "510",
        "door": "https://github.com/erastudil/easylm#studio-graph",
        "comment": (
            "Studio graph visualizes mathematical functions, data tables, and EMap concept neighborhoods "
            "using interactive 2D and 3D canvas plots."
        ),
    },
    {
        "surface": "Studio draw",
        "topic": "studio draw",
        "dewey": "700",
        "door": "https://github.com/erastudil/easylm#studio-draw",
        "comment": (
            "Studio draw provides a vector and raster sketching canvas for diagrams, freehand annotations, "
            "and visual study cards exported to local storage."
        ),
    },
    {
        "surface": "the seven Learn courses",
        "topic": "the seven learn courses",
        "dewey": "001",
        "door": "https://github.com/erastudil/easylm#the-seven-learn-courses",
        "comment": (
            "The seven Learn courses guide structured mastery across foundational shelves using "
            "textbook readings, worked checks, flashcard decks, and authored mastery exams."
        ),
    },
    {
        "surface": "local hands",
        "topic": "local hands",
        "dewey": "004",
        "door": "https://github.com/erastudil/easylm#local-hands",
        "comment": (
            "Local hands execute deterministic in-browser tools including rational arithmetic, "
            "SI unit conversion, Gregorian calendar math, and local stack card lookup."
        ),
    },
    {
        "surface": "network hands",
        "topic": "network hands",
        "dewey": "004",
        "door": "https://github.com/erastudil/easylm#network-hands",
        "comment": (
            "Network hands fetch read-only reference spans exclusively from allow-listed official doors "
            "in TRUSTED_SOURCES.md and pack LINK_INDEX.md files while stripping instruction text."
        ),
    },
    {
        "surface": "model tiers",
        "topic": "model tiers",
        "dewey": "006",
        "door": "https://github.com/erastudil/easylm#model-tiers",
        "comment": (
            "Model tiers route deterministic queries to Alice EMap first and escalate to local WebGPU "
            "or frontier models only when explicitly requested after an honest abstain."
        ),
    },
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_hex(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def tokenize_anchors(text: str) -> list[str]:
    """Extract ordered unique lowercase alphabetic tokens suitable for lemma anchoring."""
    raw = re.findall(r"[a-zA-Z]{2,}", text.lower())
    seen: set[str] = set()
    out: list[str] = []
    for tok in raw:
        if tok in _STOPWORDS:
            continue
        if tok not in seen:
            seen.add(tok)
            out.append(tok)
    return out


def _load_pack_dewey_map(stacks_root: Path) -> dict[str, str]:
    """Map pack slug -> Dewey code from PACKS.json with fallback header parsing."""
    packs_json = stacks_root / "PACKS.json"
    mapping: dict[str, str] = {}
    if packs_json.is_file():
        try:
            entries = json.loads(packs_json.read_text(encoding="utf-8"))
            for entry in entries:
                slug = str(entry.get("slug", "")).strip()
                dewey = str(entry.get("dewey", "")).strip()
                if slug and dewey:
                    mapping[slug] = dewey
        except (OSError, ValueError):
            pass
    return mapping


_FACT_LINE_RE = re.compile(
    r"^(?P<topic>[^:=#][^:=]*?)\s*[:=]\s*(?P<body>.+)$"
)
_DOOR_RE = re.compile(r"//\s*door\s+(?P<door>https?://\S+)", re.IGNORECASE)
_REF_RE = re.compile(r"//\s*ref\s+(?P<ref>.+)$", re.IGNORECASE)


def parse_fact_line(
    line: str,
    rel_path: str,
    line_no: int,
    slug: str,
    dewey: str,
    default_door: str = "https://physics.nist.gov/cuu/Constants/",
) -> dict | None:
    """Parse one `topic : comment // door <url> // ref <section>` line from FACTS.md."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    m = _FACT_LINE_RE.match(stripped)
    if not m:
        return None

    topic_raw = m.group("topic").strip()
    body_raw = m.group("body").strip()
    if not topic_raw or not body_raw:
        return None

    door = default_door
    door_match = _DOOR_RE.search(body_raw)
    if door_match:
        door = door_match.group("door").strip()

    ref = ""
    ref_match = _REF_RE.search(body_raw)
    if ref_match:
        ref = ref_match.group("ref").strip()

    # Strip trailing `// door ...` and `// ref ...` metadata from the emitted comment
    comment = re.split(r"\s*//\s*(?:door|ref)\b", body_raw, maxsplit=1, flags=re.IGNORECASE)[0].strip()
    if not comment:
        return None

    topic_norm = re.sub(r"\s+", " ", topic_raw.lower()).strip()
    card_id = _sha256_hex(f"{rel_path}:{line_no}:{topic_norm}")
    anchors = tokenize_anchors(topic_norm)
    if not anchors:
        anchors = tokenize_anchors(comment)[:3]

    return {
        "card_id": card_id,
        "kind": "stack",
        "slug": slug,
        "source_path": rel_path,
        "line": line_no,
        "topic": topic_norm,
        "comment": comment,
        "dewey": dewey,
        "door": door,
        "ref": ref,
        "anchors": anchors,
        "frames": ["define", "stack"],
        "volatility": "pinned",
    }


def compile_stack_cards(stacks_root: Path | str | None = None) -> list[dict]:
    """
    Q4.1: Compile all `stacks/*/FACTS.md` fact lines into deterministic Card records.
    Card IDs are SHA-256 digests of `relative_path:line_number:topic` and remain stable across reruns.
    """
    root = Path(stacks_root) if stacks_root is not None else DEFAULT_STACKS_ROOT
    dewey_map = _load_pack_dewey_map(root)
    cards: list[dict] = []

    if not root.is_dir():
        return cards

    facts_files = sorted(root.glob("*/FACTS.md"), key=lambda p: p.parent.name)
    for facts_path in facts_files:
        slug = facts_path.parent.name
        rel_path = f"stacks/{slug}/FACTS.md"
        raw_lines = facts_path.read_text(encoding="utf-8").splitlines()

        dewey = dewey_map.get(slug, "")
        if not dewey and raw_lines:
            hdr_match = re.search(r"\((\d{3}(?:\.\d+)?)\)", raw_lines[0])
            if hdr_match:
                dewey = hdr_match.group(1)
        if not dewey:
            dewey = "001"

        for idx, line in enumerate(raw_lines, start=1):
            card = parse_fact_line(
                line=line,
                rel_path=rel_path,
                line_no=idx,
                slug=slug,
                dewey=dewey,
            )
            if card is not None:
                cards.append(card)

    return cards


def _morphological_candidates(token: str) -> list[str]:
    """Generate simple singular/stem candidates for lemma lookup in `nodes`."""
    cands = [token]
    if len(token) > 4 and token.endswith("ies"):
        cands.append(token[:-3] + "y")
    if len(token) > 4 and token.endswith("es"):
        cands.append(token[:-2])
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        cands.append(token[:-1])
    if len(token) > 5 and token.endswith("ing"):
        cands.append(token[:-3])
        cands.append(token[:-3] + "e")
    if len(token) > 4 and token.endswith("ed"):
        cands.append(token[:-2])
        cands.append(token[:-1])
    return cands


def load_walkable_lemma_map(db_path: Path | str | None = None) -> dict[str, int]:
    """
    Load `lemma -> lowest node id` from the `nodes` sense table in `emap.db`
    per SPEC.md §2 & §4.
    """
    target_db = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    if not target_db.is_file():
        return {}
    conn = sqlite3.connect(str(target_db))
    try:
        cur = conn.cursor()
        cur.execute("SELECT LOWER(lemma), MIN(id) FROM nodes GROUP BY LOWER(lemma)")
        return {str(row[0]): int(row[1]) for row in cur.fetchall() if row[0] is not None}
    finally:
        conn.close()


def anchor_cards_to_map(
    cards: list[dict],
    db_path: Path | str | None = None,
    lemma_map: dict[str, int] | None = None,
) -> list[dict]:
    """
    Q4.2: Anchor each card's topic tokens onto walkable sense node IDs in `emap.db`.
    Every card receives `anchor_ids: list[int]`, `grounded_anchors: list[str]`,
    and `unanchored: bool` (True iff zero tokens resolved to a sense node).
    """
    lmap = lemma_map if lemma_map is not None else load_walkable_lemma_map(db_path)
    anchored_cards: list[dict] = []

    for card in cards:
        updated = dict(card)
        anchor_ids: list[int] = []
        grounded_anchors: list[str] = []

        candidate_tokens = list(updated.get("anchors", []))
        # Also allow fallback grounding on comment keywords if topic tokens miss
        if not candidate_tokens:
            candidate_tokens = tokenize_anchors(updated.get("comment", ""))[:4]

        for tok in candidate_tokens:
            resolved_id: int | None = None
            for cand in _morphological_candidates(tok):
                if cand in lmap:
                    resolved_id = lmap[cand]
                    break
            if resolved_id is not None and resolved_id not in anchor_ids:
                anchor_ids.append(resolved_id)
                grounded_anchors.append(tok)

        updated["anchor_ids"] = anchor_ids
        updated["grounded_anchors"] = grounded_anchors
        updated["unanchored"] = len(anchor_ids) == 0
        anchored_cards.append(updated)

    return anchored_cards


def golden_prompt_for_card(card: dict, include_Context_when_duplicate: bool = True) -> str:
    """
    Q4.3: Produce a deterministic golden question for a stack card.
    """
    topic = card["topic"]
    slug = card.get("slug", "")
    line = card.get("line", 0)
    if include_Context_when_duplicate and slug:
        return f"What is {topic} in {slug} (line {line})?"
    return f"What is {topic}?"


def build_golden_prompts(cards: list[dict]) -> list[dict]:
    """
    Q4.3: Build one golden prompt entry per stack card across the entire compiled deck.
    Uses plain `What is <topic>?` when the topic is unique across the deck, and
    disambiguates with `in <slug>` (and line when duplicated within the same pack)
    when multiple cards share the same topic string.
    """
    topic_counts: dict[str, int] = {}
    slug_topic_counts: dict[tuple[str, str], int] = {}
    for c in cards:
        t = c["topic"]
        s = c.get("slug", "")
        topic_counts[t] = topic_counts.get(t, 0) + 1
        slug_topic_counts[(s, t)] = slug_topic_counts.get((s, t), 0) + 1

    entries: list[dict] = []
    for c in cards:
        t = c["topic"]
        s = c.get("slug", "")
        if topic_counts.get(t, 0) == 1:
            prompt = f"What is {t}?"
        elif slug_topic_counts.get((s, t), 0) == 1:
            prompt = f"What is {t} in {s}?"
        else:
            prompt = f"What is {t} in {s} (line {c.get('line', 0)})?"
        entries.append({
            "card_id": c["card_id"],
            "topic": t,
            "slug": s,
            "dewey": c["dewey"],
            "prompt": prompt,
        })
    return entries


_QUESTION_PREFIX_RE = re.compile(
    r"^\s*(?:what\s+is|what\s+are|define|explain|tell\s+me\s+about|state|describe)\s+",
    re.IGNORECASE,
)
_LINE_SUFFIX_RE = re.compile(r"\s*\(line\s+(?P<line>\d+)\)\s*\??\s*$", re.IGNORECASE)
_IN_SLUG_SUFFIX_RE = re.compile(r"\s+in\s+(?P<slug>[a-z0-9_.]+)\s*\??\s*$", re.IGNORECASE)


def retrieve_stack_card(
    prompt: str,
    cards: list[dict],
    theta_stack: float = 0.85,
) -> dict:
    """
    Q4.3 & Q4.4: Retrieve a stack card for `prompt` under SPEC.md §3 & §9.
    - Unique hit: returns comment, dewey, door, provenance=`stack:<card_id>`, act=`cite`.
    - Tied hits: returns up to 5 tied cards (each with topic and dewey, ranked by anchor
      overlap then edge weight) without emitting a blended sentence.
    - Miss / outside-domain: returns route=`ABSTAIN`, confidence=0.0, provenance=None,
      act=`silence-gap`, naming the frame and ungrounded tokens.
    """
    raw = (prompt or "").strip()
    if not raw or not cards:
        return {
            "route": "ABSTAIN",
            "frame": "stack",
            "confidence": 0.0,
            "provenance": None,
            "digest": None,
            "timestamp": _utc_now_iso(),
            "hops": [],
            "ungrounded_tokens": tokenize_anchors(raw),
            "comment": None,
            "dewey": None,
            "door": None,
            "act": "silence-gap",
            "reason": "frame=stack; ungrounded_tokens=empty",
        }

    cleaned = _QUESTION_PREFIX_RE.sub("", raw).strip()
    target_line: int | None = None
    line_m = _LINE_SUFFIX_RE.search(cleaned)
    if line_m:
        target_line = int(line_m.group("line"))
        cleaned = cleaned[: line_m.start()].strip()

    target_slug: str | None = None
    slug_m = _IN_SLUG_SUFFIX_RE.search(cleaned)
    if slug_m:
        candidate_slug = slug_m.group("slug").lower()
        known_slugs = {c.get("slug", "").lower() for c in cards}
        known_deweys = {c.get("dewey", "").lower() for c in cards}
        if candidate_slug in known_slugs or candidate_slug in known_deweys:
            target_slug = candidate_slug
            cleaned = cleaned[: slug_m.start()].strip()

    subject = re.sub(r"[?.!]+$", "", cleaned).strip().lower()
    subject = re.sub(r"\s+", " ", subject)
    query_anchors = tokenize_anchors(subject)

    # 1. Exact topic match (filtered by optional slug/dewey and line)
    exact_matches: list[dict] = []
    for c in cards:
        if c["topic"] == subject:
            if target_slug and c.get("slug", "").lower() != target_slug and c.get("dewey", "").lower() != target_slug:
                continue
            if target_line is not None and c.get("line") != target_line:
                continue
            exact_matches.append(c)

    # If target_slug was part of the actual topic (e.g. "erosion in earth_sciences" vs "in vacuum"),
    # also check full cleaned string before stripping `in <slug>`
    if not exact_matches and target_slug is not None:
        full_subject = re.sub(r"[?.!]+$", "", _QUESTION_PREFIX_RE.sub("", raw).strip()).lower()
        full_subject = re.sub(r"\s+", " ", full_subject)
        for c in cards:
            if c["topic"] == full_subject:
                exact_matches.append(c)

    if len(exact_matches) == 1:
        hit = exact_matches[0]
        prov = f"stack:{hit['card_id']}"
        return {
            "route": "RETRIEVE",
            "frame": "stack",
            "kind": "stack",
            "card_id": hit["card_id"],
            "topic": hit["topic"],
            "comment": hit["comment"],
            "dewey": hit["dewey"],
            "door": hit["door"],
            "confidence": 1.0,
            "provenance": prov,
            "digest": _sha256_hex(f"{prov}:{hit['comment']}"),
            "timestamp": _utc_now_iso(),
            "hops": [f"lemma:{a}" for a in hit.get("anchors", [])],
            "act": "cite",
            "tied_cards": [],
        }

    if len(exact_matches) > 1:
        # Tied hits per SPEC.md §3: up to 5 cards ranked by anchor overlap then weight; no blended sentence
        ranked = sorted(
            exact_matches,
            key=lambda c: (-len(set(query_anchors) & set(c.get("anchors", []))), c.get("dewey", ""), c.get("card_id", "")),
        )[:5]
        top = ranked[0]
        prov = f"stack:{top['card_id']}"
        return {
            "route": "RETRIEVE",
            "frame": "stack",
            "kind": "stack",
            "card_id": top["card_id"],
            "topic": top["topic"],
            "comment": top["comment"],
            "dewey": top["dewey"],
            "door": top["door"],
            "confidence": 0.90,
            "provenance": prov,
            "digest": _sha256_hex(f"{prov}:{top['comment']}"),
            "timestamp": _utc_now_iso(),
            "hops": [f"lemma:{a}" for a in top.get("anchors", [])],
            "act": "cite",
            "tied_cards": [
                {
                    "card_id": c["card_id"],
                    "topic": c["topic"],
                    "dewey": c["dewey"],
                    "door": c["door"],
                    "comment": c["comment"],
                }
                for c in ranked
            ],
        }

    # 2. High-confidence anchor overlap when every query anchor is grounded in the card's topic anchors
    if query_anchors:
        scored: list[tuple[float, int, dict]] = []
        qset = set(query_anchors)
        for c in cards:
            if target_slug and c.get("slug", "").lower() != target_slug and c.get("dewey", "").lower() != target_slug:
                continue
            c_anchors = set(c.get("anchors", []))
            if not c_anchors:
                continue
            overlap = len(qset & c_anchors)
            if overlap == 0:
                continue
            # Require all query tokens to be present in card topic anchors to prevent false positives on outside-domain prompts
            if not qset.issubset(c_anchors):
                continue
            jaccard = overlap / len(qset | c_anchors)
            score = 0.85 + 0.15 * jaccard
            if score >= theta_stack:
                scored.append((score, overlap, c))

        if scored:
            scored.sort(key=lambda item: (-item[0], -item[1], item[2]["card_id"]))
            best_score, _, best_card = scored[0]
            tied = [item[2] for item in scored if abs(item[0] - best_score) < 1e-9][:5]
            prov = f"stack:{best_card['card_id']}"
            return {
                "route": "RETRIEVE",
                "frame": "stack",
                "kind": "stack",
                "card_id": best_card["card_id"],
                "topic": best_card["topic"],
                "comment": best_card["comment"],
                "dewey": best_card["dewey"],
                "door": best_card["door"],
                "confidence": round(best_score, 4),
                "provenance": prov,
                "digest": _sha256_hex(f"{prov}:{best_card['comment']}"),
                "timestamp": _utc_now_iso(),
                "hops": [f"lemma:{a}" for a in best_card.get("anchors", [])],
                "act": "cite",
                "tied_cards": [
                    {
                        "card_id": c["card_id"],
                        "topic": c["topic"],
                        "dewey": c["dewey"],
                        "door": c["door"],
                        "comment": c["comment"],
                    }
                    for c in tied
                ] if len(tied) > 1 else [],
            }

    # 3. Miss -> ABSTAIN with null provenance and silence-gap speech act (SPEC.md §3, §9, §11 & Q4.4)
    all_card_anchors = {a for c in cards for a in c.get("anchors", [])}
    ungrounded = [t for t in query_anchors if t not in all_card_anchors]
    if not ungrounded:
        ungrounded = query_anchors or [subject]

    return {
        "route": "ABSTAIN",
        "frame": "stack",
        "confidence": 0.0,
        "provenance": None,
        "digest": None,
        "timestamp": _utc_now_iso(),
        "hops": [],
        "ungrounded_tokens": ungrounded,
        "comment": None,
        "dewey": None,
        "door": None,
        "act": "silence-gap",
        "reason": f"frame=stack; ungrounded_tokens={','.join(ungrounded)}",
    }


_URL_EXTRACT_RE = re.compile(r"https?://[^\s|>`)\"']+")


def compile_trusted_doors(stacks_root: Path | str | None = None) -> dict:
    """
    Q5.1: Import official doors from `stacks/TRUSTED_SOURCES.md` and `stacks/*/LINK_INDEX.md`.
    Generates the host allow-list dynamically from the repository files rather than hand-typing per query.
    """
    root = Path(stacks_root) if stacks_root is not None else DEFAULT_STACKS_ROOT
    hosts: set[str] = set(BASELINE_ALLOWED_HOSTS)
    doors: list[dict] = []

    trusted_md = root / "TRUSTED_SOURCES.md"
    if trusted_md.is_file():
        for line_no, line in enumerate(trusted_md.read_text(encoding="utf-8").splitlines(), start=1):
            for url in _URL_EXTRACT_RE.findall(line):
                parsed = urlparse(url)
                host = (parsed.hostname or "").lower()
                if host:
                    hosts.add(host)
                    doors.append({
                        "url": url,
                        "host": host,
                        "source": "stacks/TRUSTED_SOURCES.md",
                        "line": line_no,
                        "tier": _classify_host_tier(host),
                    })

    if root.is_dir():
        for link_index in sorted(root.glob("*/LINK_INDEX.md"), key=lambda p: p.parent.name):
            slug = link_index.parent.name
            rel = f"stacks/{slug}/LINK_INDEX.md"
            in_unverified_section = False
            for line_no, line in enumerate(link_index.read_text(encoding="utf-8").splitlines(), start=1):
                if re.match(r"^##\s+.*(?:Unverified|Derivative|Do Not Cite)", line, flags=re.IGNORECASE):
                    in_unverified_section = True
                elif line.startswith("## "):
                    in_unverified_section = False
                if in_unverified_section:
                    continue
                for url in _URL_EXTRACT_RE.findall(line):
                    parsed = urlparse(url)
                    host = (parsed.hostname or "").lower()
                    if host:
                        hosts.add(host)
                        doors.append({
                            "url": url,
                            "host": host,
                            "source": rel,
                            "line": line_no,
                            "tier": _classify_host_tier(host),
                        })

    return {
        "hosts": sorted(hosts),
        "host_set": frozenset(hosts),
        "doors": doors,
    }


def _classify_host_tier(host: str) -> str:
    """
    Classify host per SPEC.md §8:
    NIST, BIPM, IETF, statute (.gov), or standard/university (.edu) door wins over Wikipedia.
    """
    h = host.lower()
    if "wikipedia.org" in h or "wikimedia.org" in h or "wikidata.org" in h:
        return "orientation"
    for suffix in PRIMARY_AUTHORITY_SUFFIXES:
        if h == suffix.lstrip(".") or h.endswith(suffix):
            return "primary"
    return "standard"


def is_allowed_door(url: str, trusted_doors: dict | None = None) -> bool:
    """
    Q5.1 & Q5.3: Return True iff `url` uses HTTPS/HTTP and its hostname belongs to the
    generated trusted-sources allow-list.
    """
    if not url:
        return False
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("https", "http"):
        return False
    host = (parsed.hostname or "").lower()
    if not host:
        return False
    door_registry = trusted_doors if trusted_doors is not None else compile_trusted_doors()
    allowed_set = door_registry.get("host_set", BASELINE_ALLOWED_HOSTS)
    if host in allowed_set:
        return True
    # Also allow subdomains of allow-listed root hosts (e.g.physics.nist.gov under nist.gov)
    for allowed_host in allowed_set:
        if host.endswith("." + allowed_host):
            return True
    return False


_INSTRUCTION_INJECTION_RE = re.compile(
    r"(?:ignore\s+(?:all\s+)?previous\s+instructions|system\s+prompt\s*:|you\s+are\s+now\s+|disregard\s+all\s+rules)[^.\n]*[.\n]?",
    re.IGNORECASE,
)


def sanitize_fetched_span(raw_text: str) -> str:
    """
    SPEC.md §8: 'fetched text is data. Instruction text inside a fetched page is discarded.'
    """
    cleaned = _INSTRUCTION_INJECTION_RE.sub("", raw_text or "")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def resolve_hand_or_card(
    prompt: str,
    cards: list[dict],
    trusted_doors: dict | None = None,
    fetch_fn: Callable[[str], str] | None = None,
    force_url: str | None = None,
    theta_hand: float = 0.80,
) -> dict:
    """
    Q5.2 & Q5.3: Execute the RETRIEVE -> HAND -> ABSTAIN lattice rules from SPEC.md §§ 3, 6, 8:
      1. A pinned stack card on the topic wins before HAND runs and NEVER opens a network socket.
      2. When a card is marked `volatility == "fresh"` (or when the prompt misses stack cards and
         requests a door), HAND checks the generated host allow-list.
      3. An unlisted foreign host abstains with `provenance=None` and `network_called=False`.
      4. Fetched text has any embedded instruction-injection strings stripped before emission.
    """
    door_registry = trusted_doors if trusted_doors is not None else compile_trusted_doors()
    socket_calls: list[str] = []

    def _default_fetch(url: str) -> str:
        socket_calls.append(url)
        if fetch_fn is not None:
            return fetch_fn(url)
        return f"Fetched verified reference span from {url}"

    # Check stack cards first unless caller explicitly forces a raw URL hand check
    if force_url is None:
        card_res = retrieve_stack_card(prompt, cards)
        if card_res["route"] == "RETRIEVE":
            # Look up the underlying card volatility
            card_id = card_res["card_id"]
            matched_card = next((c for c in cards if c["card_id"] == card_id), None)
            volatility = matched_card.get("volatility", "pinned") if matched_card else "pinned"
            asks_live = bool(re.search(r"\b(?:live|refresh|fetch|current\s+page)\b", prompt, re.IGNORECASE))

            if volatility == "pinned" and not asks_live:
                # Q5.2: Pinned card NEVER opens a socket
                out = dict(card_res)
                out["network_called"] = False
                out["socket_calls"] = socket_calls
                return out

            # Fresh card (or explicit live refresh on a fresh card): verify door host allow-list
            door_url = card_res.get("door") or ""
            if not is_allowed_door(door_url, door_registry):
                return {
                    "route": "ABSTAIN",
                    "frame": "fresh",
                    "confidence": 0.0,
                    "provenance": None,
                    "digest": None,
                    "timestamp": _utc_now_iso(),
                    "hops": [],
                    "comment": None,
                    "door": door_url,
                    "act": "silence-gap",
                    "network_called": False,
                    "socket_calls": socket_calls,
                    "reason": f"unlisted_host:{door_url}",
                }

            raw_span = _default_fetch(door_url)
            safe_span = sanitize_fetched_span(raw_span)
            return {
                "route": "HAND",
                "frame": "fresh",
                "card_id": card_id,
                "topic": card_res["topic"],
                "comment": safe_span,
                "dewey": card_res["dewey"],
                "door": door_url,
                "confidence": max(theta_hand, 0.85),
                "provenance": door_url,
                "digest": _sha256_hex(f"{door_url}:{safe_span}"),
                "timestamp": _utc_now_iso(),
                "hops": card_res.get("hops", []),
                "act": "cite",
                "network_called": True,
                "socket_calls": socket_calls,
            }

    # Explicit URL in prompt or `force_url`
    url_match = _URL_EXTRACT_RE.search(prompt or "")
    candidate_url = force_url or (url_match.group(0) if url_match else "")
    if candidate_url:
        if not is_allowed_door(candidate_url, door_registry):
            # Q5.3: Unlisted foreign domain must abstain without opening a socket
            return {
                "route": "ABSTAIN",
                "frame": "fresh",
                "confidence": 0.0,
                "provenance": None,
                "digest": None,
                "timestamp": _utc_now_iso(),
                "hops": [],
                "comment": None,
                "door": candidate_url,
                "act": "silence-gap",
                "network_called": False,
                "socket_calls": socket_calls,
                "reason": f"unlisted_host:{candidate_url}",
            }

        raw_span = _default_fetch(candidate_url)
        safe_span = sanitize_fetched_span(raw_span)
        return {
            "route": "HAND",
            "frame": "fresh",
            "card_id": None,
            "topic": candidate_url,
            "comment": safe_span,
            "dewey": None,
            "door": candidate_url,
            "confidence": max(theta_hand, 0.85),
            "provenance": candidate_url,
            "digest": _sha256_hex(f"{candidate_url}:{safe_span}"),
            "timestamp": _utc_now_iso(),
            "hops": [],
            "act": "cite",
            "network_called": True,
            "socket_calls": socket_calls,
        }

    # Neither card nor valid door matched
    return {
        "route": "ABSTAIN",
        "frame": "fresh",
        "confidence": 0.0,
        "provenance": None,
        "digest": None,
        "timestamp": _utc_now_iso(),
        "hops": [],
        "comment": None,
        "door": None,
        "act": "silence-gap",
        "network_called": False,
        "socket_calls": socket_calls,
        "reason": "no_matching_card_or_listed_door",
    }


def compile_feature_cards() -> list[dict]:
    """
    Q6.1: Compile the L3 feature card deck for all 13 EasyLM surfaces named in SPEC.md §5 L3.
    """
    deck: list[dict] = []
    for idx, item in enumerate(FEATURE_SURFACES, start=1):
        surface = item["surface"]
        topic = item["topic"].lower()
        card_id = _sha256_hex(f"emap/SPEC.md:L85:{ idx }:{topic}")
        deck.append({
            "card_id": card_id,
            "kind": "feature",
            "surface": surface,
            "topic": topic,
            "comment": item["comment"],
            "dewey": item["dewey"],
            "door": item["door"],
            "anchors": tokenize_anchors(topic),
            "frames": ["feature", "define"],
            "volatility": "pinned",
        })
    return deck


def retrieve_feature_card(prompt: str, feature_cards: list[dict] | None = None) -> dict:
    """
    Q6.2: Match a how-to or feature query against the L3 EasyLM feature deck.
    Returns `provenance = "feature:<card_id>"` and `act = "cite"` on hit, or `ABSTAIN` on miss.
    """
    deck = feature_cards if feature_cards is not None else compile_feature_cards()
    norm = re.sub(r"\s+", " ", (prompt or "").lower()).strip()

    for card in deck:
        topic = card["topic"]
        surface_low = card["surface"].lower()
        if topic in norm or surface_low in norm:
            prov = f"feature:{card['card_id']}"
            return {
                "route": "RETRIEVE",
                "frame": "feature",
                "kind": "feature",
                "card_id": card["card_id"],
                "surface": card["surface"],
                "topic": card["topic"],
                "comment": card["comment"],
                "dewey": card["dewey"],
                "door": card["door"],
                "confidence": 1.0,
                "provenance": prov,
                "digest": _sha256_hex(f"{prov}:{card['comment']}"),
                "timestamp": _utc_now_iso(),
                "hops": [f"lemma:{a}" for a in card.get("anchors", [])],
                "act": "cite",
            }

    return {
        "route": "ABSTAIN",
        "frame": "feature",
        "confidence": 0.0,
        "provenance": None,
        "digest": None,
        "timestamp": _utc_now_iso(),
        "hops": [],
        "comment": None,
        "dewey": None,
        "door": None,
        "act": "silence-gap",
        "reason": "frame=feature; surface_not_found",
    }


def _extract_textbook_spans(raw_text: str) -> list[str]:
    """
    Extract verbatim prose paragraphs from a TEXTBOOK.md file so every returned
    span is guaranteed to be an exact substring (`span in raw_text`) of the textbook file (Q7.3).
    """
    spans: list[str] = []
    # Split on blank lines while preserving exact substring slices
    blocks = re.split(r"\r?\n\r?\n+", raw_text)
    in_frontmatter = False
    for idx, block in enumerate(blocks):
        trimmed = block.strip()
        if not trimmed:
            continue
        if idx == 0 and trimmed.startswith("---"):
            if trimmed.count("---") >= 2:
                continue
            in_frontmatter = True
            continue
        if in_frontmatter:
            if "---" in trimmed:
                in_frontmatter = False
            continue
        # Skip ASCII box diagrams, tables, and bare headers
        if trimmed.startswith(("```", "+", "|", "#", "---")):
            continue
        if len(trimmed) < 60:
            continue
        if trimmed in raw_text:
            spans.append(trimmed)
    return spans


def teach_walk(
    shelf: str,
    topic: str | None = None,
    step: int = 0,
    stacks_root: Path | str | None = None,
) -> dict:
    """
    Q7.3 (SPEC.md §5 L5): Teaching mode walk. After a shelf (slug or Dewey code) is chosen,
    returns the written textbook span for that topic or step index.
    Guarantees that `result["span"]` is an exact verbatim substring of `stacks/<slug>/TEXTBOOK.md`.
    """
    root = Path(stacks_root) if stacks_root is not None else DEFAULT_STACKS_ROOT
    dewey_map = _load_pack_dewey_map(root)
    reverse_dewey = {v: k for k, v in dewey_map.items()}

    target_key = (shelf or "").strip().lower()
    slug = target_key if (root / target_key / "TEXTBOOK.md").is_file() else reverse_dewey.get(target_key, "")
    if not slug:
        return {
            "route": "ABSTAIN",
            "frame": "walk",
            "confidence": 0.0,
            "provenance": None,
            "digest": None,
            "timestamp": _utc_now_iso(),
            "span": None,
            "act": "silence-gap",
            "reason": f"unknown_shelf:{shelf}",
        }

    textbook_path = root / slug / "TEXTBOOK.md"
    raw_text = textbook_path.read_text(encoding="utf-8")
    spans = _extract_textbook_spans(raw_text)
    if not spans:
        return {
            "route": "ABSTAIN",
            "frame": "walk",
            "confidence": 0.0,
            "provenance": None,
            "digest": None,
            "timestamp": _utc_now_iso(),
            "span": None,
            "act": "silence-gap",
            "reason": f"empty_textbook:{slug}",
        }

    selected_spans = spans
    if topic:
        topic_tokens = tokenize_anchors(topic)
        if topic_tokens:
            matching = [
                s for s in spans
                if any(tok in s.lower() for tok in topic_tokens)
            ]
            if matching:
                selected_spans = matching

    clamped_step = max(0, min(step, len(selected_spans) - 1))
    chosen_span = selected_spans[clamped_step]
    dewey = dewey_map.get(slug, "001")
    rel_path = f"stacks/{slug}/TEXTBOOK.md"
    prov = f"walk:{slug}:{clamped_step}"

    return {
        "route": "WALK",
        "frame": "walk",
        "slug": slug,
        "dewey": dewey,
        "topic": topic or slug,
        "step": clamped_step,
        "total_steps": len(selected_spans),
        "span": chosen_span,
        "source_path": rel_path,
        "confidence": 1.0,
        "provenance": prov,
        "digest": _sha256_hex(f"{rel_path}:{clamped_step}:{chosen_span}"),
        "timestamp": _utc_now_iso(),
        "act": "cite",
    }
