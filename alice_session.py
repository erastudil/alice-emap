"""One Alice turn for Hydra and for the EasyLM web path.

She reads the prompt in layers first: speech act, frame, slots, instrument, authority, shelves.
Memory commands run before any of that fires.
An orchestration frame cites the Hydra command and does not launch it.
A sense frame runs the local instrument and reads the result back.
Everything else walks compute, the lexicon, stack cards, feature cards, knowledge cards, then the whitelist.
A personality is carried on the receipt. It does not rewrite the sentence.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Optional

from alice_cards import search_features, search_stacks
from alice_decision_engine import (
    AliceDecisionEngine,
    DeterministicEngine,
    WhitelistedHandProxy,
)
from alice_interpret import Reading, interpret
from alice_knowledge import search_knowledge
from alice_memory import MemoryStore
from alice_personalities import mandate_for, resolve_personality
from alice_senses import browse, hear_audio, search_code, see_image, write_drawing

REMEMBER = re.compile(
    r"^remember(?:\s+(rule|goal|preference|fact|insight))?\s*:\s*(.+)$",
    flags=re.IGNORECASE,
)
FORGET = re.compile(r"^forget\s*:\s*(.+)$", flags=re.IGNORECASE)
RECALL = re.compile(
    r"^(?:what do you remember|show memory|memory search)(?:\s+about\s+(.+))?$",
    flags=re.IGNORECASE,
)


def _format_memory(atoms: list) -> str:
    if not atoms:
        return ""
    lines = [f"- [{atom['kind']}] {atom['text']}" for atom in atoms]
    return "\n".join(lines)


def _receipt(
    *,
    act: str,
    route: str,
    answer: str,
    source: str,
    personality: str,
    memory: list,
    shelves: list,
    next_shelf: str,
    provenance: Optional[dict] = None,
    frame: str = "",
    tool: str = "",
    command: str = "",
    layers: Optional[list] = None,
) -> dict:
    return {
        "act": act,
        "route": route,
        "answer": answer,
        "source": source,
        "personality": personality,
        "mandate": mandate_for(personality),
        "memory": memory,
        "shelves": shelves,
        "next": next_shelf,
        "provenance": provenance,
        "frame": frame,
        "tool": tool,
        "command": command,
        "layers": list(layers or []),
    }


def run_turn(
    query: str,
    personality: str = "chat",
    memory_path: Optional[Path] = None,
    cards_path: Optional[Path] = None,
    engine: Optional[AliceDecisionEngine] = None,
    drawing_dir: Optional[Path] = None,
    workspace: Optional[Path] = None,
) -> dict:
    personality_id = resolve_personality(personality)
    text = query.strip()
    store = MemoryStore(memory_path) if memory_path else None
    try:
        return _run_turn(
            text,
            personality_id,
            store,
            cards_path,
            engine or AliceDecisionEngine(),
            drawing_dir,
            workspace or Path.cwd(),
        )
    finally:
        if store:
            store.close()


def _run_turn(
    text,
    personality_id,
    store,
    cards_path,
    engine: AliceDecisionEngine,
    drawing_dir: Optional[Path],
    workspace: Path,
) -> dict:
    reading = interpret(text, personality_id)
    shelves = ["memory"]
    memory_hits = store.search(text) if store else []

    def finish(**kwargs) -> dict:
        kwargs.setdefault("frame", reading.frame)
        kwargs.setdefault("tool", reading.tool)
        kwargs.setdefault("command", reading.command)
        kwargs.setdefault("layers", reading.layers)
        return _receipt(**kwargs)

    remembered = REMEMBER.match(text)
    if remembered and store:
        kind = (remembered.group(1) or "fact").lower()
        body = remembered.group(2).strip()
        atom = store.add(body, kind=kind, personality=personality_id)
        return finish(
            act="say",
            route="MEMORY",
            answer=f"Kept a {atom['kind']}: {atom['text']}",
            source=f"memory:{atom['id']}",
            personality=personality_id,
            memory=[atom],
            shelves=shelves,
            next_shelf="",
        )

    forgotten = FORGET.match(text)
    if forgotten and store:
        count = store.forget(forgotten.group(1))
        return finish(
            act="say",
            route="MEMORY",
            answer=f"Forgot {count} note{'s' if count != 1 else ''}.",
            source="memory:forget",
            personality=personality_id,
            memory=[],
            shelves=shelves,
            next_shelf="",
        )

    recall = RECALL.match(text)
    if recall and store:
        needle = recall.group(1) or text
        found = store.search(needle)
        if not found:
            return finish(
                act="silence-gap",
                route="ABSTAIN",
                answer="No memory notes matched.",
                source="",
                personality=personality_id,
                memory=[],
                shelves=shelves,
                next_shelf="remember a note, or ask a stack",
            )
        return finish(
            act="say",
            route="MEMORY",
            answer=_format_memory(found),
            source="memory:search",
            personality=personality_id,
            memory=found,
            shelves=shelves,
            next_shelf="",
        )

    acted = _act_on_frame(reading, text, personality_id, memory_hits, shelves, drawing_dir, workspace)
    if acted:
        return finish(**acted)

    shelves.append("compute")
    computed = _compute(text)
    if computed:
        answer, source, digest = computed
        return finish(
            act="say",
            route="COMPUTE",
            answer=answer,
            source=source,
            personality=personality_id,
            memory=memory_hits,
            shelves=shelves,
            next_shelf="",
            provenance={"source": source, "digest": digest},
        )

    shelves.append("lexicon")
    nav = engine.navigator.query_graph(text)
    if nav:
        answer, confidence, _meta = nav
        if confidence >= engine.theta_stack:
            return finish(
                act="cite",
                route="RETRIEVE",
                answer=answer,
                source="lexicon",
                personality=personality_id,
                memory=memory_hits,
                shelves=shelves,
                next_shelf="",
            )

    shelves.append("stacks")
    stack_hits = search_stacks(text, cards_path=cards_path, limit=1)
    if stack_hits:
        card = stack_hits[0]
        door = f" Door: {card['door']}" if card.get("door") else ""
        answer = (
            f"{card['topic']}: {card['comment']} "
            f"[Dewey {card['dewey']} · {card['title']}]{door}"
        )
        return finish(
            act="cite",
            route="RETRIEVE",
            answer=answer,
            source=f"stack:{card['card_id']}",
            personality=personality_id,
            memory=memory_hits,
            shelves=shelves,
            next_shelf="",
        )

    shelves.append("features")
    feature = search_features(text)
    if feature:
        return finish(
            act="cite",
            route="RETRIEVE",
            answer=feature["comment"],
            source=feature["card_id"],
            personality=personality_id,
            memory=memory_hits,
            shelves=shelves,
            next_shelf="",
        )

    if "knowledge" in reading.shelves or reading.frame in {"ask", "code", "procedure"}:
        shelves.append("knowledge")
        known = search_knowledge(text)
        if known:
            return finish(
                act="cite",
                route="RETRIEVE",
                answer=f"{known['topic']}: {known['comment']}",
                source=known["card_id"],
                personality=personality_id,
                memory=memory_hits,
                shelves=shelves,
                next_shelf="",
            )

    shelves.append("hand")
    hand = WhitelistedHandProxy.query_hand(text)
    if hand:
        answer, trust, meta = hand
        if trust >= engine.theta_hand:
            return finish(
                act="cite",
                route="HAND",
                answer=answer,
                source=meta["url"],
                personality=personality_id,
                memory=memory_hits,
                shelves=shelves,
                next_shelf="",
            )

    return finish(
        act="silence-gap",
        route="ABSTAIN",
        answer="No stack card, feature card, or tool covered that.",
        source="",
        personality=personality_id,
        memory=memory_hits,
        shelves=shelves,
        next_shelf="name a stack subject, or ask for a sample",
    )


def _act_on_frame(reading: Reading, text, personality_id, memory_hits, shelves, drawing_dir, workspace) -> Optional[dict]:
    """Run an instrument, or cite a command. None means the shelves still have to walk."""
    if reading.frame in {"swarm", "agent", "mcp", "serve"}:
        shelves.append(reading.frame)
        return {
            "act": "cite",
            "route": "ORCHESTRATE",
            "answer": reading.command,
            "source": reading.shelves[0] if reading.shelves else reading.tool,
            "personality": personality_id,
            "memory": memory_hits,
            "shelves": shelves,
            "next_shelf": "run that command yourself; Alice does not launch a paid swarm or a frontier agent",
        }
    if reading.frame == "browse":
        shelves.append("browse")
        result = browse(reading.subject)
        return _sense_receipt(result, personality_id, memory_hits, shelves, reading.command)
    if reading.frame == "see":
        shelves.append("see")
        result = see_image(Path(reading.subject))
        return _sense_receipt(result, personality_id, memory_hits, shelves, "")
    if reading.frame == "hear":
        shelves.append("hear")
        result = hear_audio(Path(reading.subject))
        return _sense_receipt(result, personality_id, memory_hits, shelves, "")
    if reading.frame == "draw":
        shelves.append("draw")
        dest_dir = drawing_dir or Path(tempfile.gettempdir()) / "alice-drawings"
        result = write_drawing(text, dest_dir / "drawing.svg")
        svg = result.get("svg") or ""
        answer = result["answer"] if not svg else result["answer"] + "\n" + svg
        return _sense_receipt(
            {**result, "answer": answer},
            personality_id,
            memory_hits,
            shelves,
            "",
        )
    if reading.frame == "search":
        shelves.append("search")
        result = search_code(reading.subject, workspace)
        return _sense_receipt(result, personality_id, memory_hits, shelves, reading.command)
    return None


def _sense_receipt(result: dict, personality_id: str, memory_hits: list, shelves: list, command: str) -> dict:
    ok = bool(result.get("ok"))
    return {
        "act": result["act"],
        "route": "SENSE" if ok else "ABSTAIN",
        "answer": result["answer"],
        "source": result["source"],
        "personality": personality_id,
        "memory": memory_hits,
        "shelves": shelves,
        "next_shelf": result.get("next") or "",
        "command": command,
    }


def _compute(text: str):
    cas = DeterministicEngine.evaluate_cas_rational(text)
    if cas:
        answer, digest = cas
        return f"Result: {answer}", "tool:cas_rational_kernel", digest
    units = DeterministicEngine.evaluate_si_dimensions(text)
    if units:
        answer, digest = units
        source = "tool:si_dimension_checker" if "DIMENSIONAL_TYPE_ERROR" in answer else "tool:si_units_algebra"
        prefix = "Error" if "DIMENSIONAL_TYPE_ERROR" in answer else "Conversion"
        return f"{prefix}: {answer}", source, digest
    clock = DeterministicEngine.evaluate_proleptic_gregorian(text)
    if clock:
        answer, digest = clock
        return f"Datetime: {answer}", "tool:datetime_gregorian", digest
    return None


def format_turn(turn: dict) -> str:
    lines = [
        f"act: {turn['act']}",
        f"route: {turn['route']}",
        f"frame: {turn.get('frame') or '-'}",
        f"personality: {turn['personality']}",
        f"source: {turn['source'] or '-'}",
        f"answer: {turn['answer']}",
    ]
    if turn.get("command"):
        lines.append(f"command: {turn['command']}")
    if turn.get("next"):
        lines.append(f"next: {turn['next']}")
    if turn.get("layers"):
        lines.append("layers:")
        lines.extend(f"  {line}" for line in turn["layers"])
    if turn.get("memory") and turn["route"] not in {"MEMORY"}:
        lines.append("memory:")
        lines.append(_format_memory(turn["memory"]))
    return "\n".join(lines)


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description="Alice session turn")
    parser.add_argument("query", nargs="+", help="The question")
    parser.add_argument("--personality", default="chat")
    parser.add_argument("--memory", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        turn = run_turn(" ".join(args.query), personality=args.personality, memory_path=args.memory)
    except KeyError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2
    if args.json:
        print(json.dumps(turn, indent=2))
    else:
        print(format_turn(turn))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
