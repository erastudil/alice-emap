"""Compile EasyLM stacks/*/FACTS.md into stack cards.

Each fact line is one card. The comment is the sentence Alice may cite.
The door is the URL on that line. Cards are pinned.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

LINE = re.compile(r"^(?P<topic>.+?)\s+(?P<mark>[=:])\s+(?P<rest>.+?)\s*$")
DOOR = re.compile(r"https?://\S+")


def _split_rest(rest: str) -> tuple[str, str]:
    parts = re.split(r"\s+//\s+", rest, maxsplit=2)
    comment = parts[0].strip()
    door = ""
    for part in parts[1:]:
        found = DOOR.search(part)
        if found and not door:
            door = found.group(0).rstrip(".,)")
            break
    return comment, door


def compile_stacks(stacks_root: Path) -> list[dict]:
    packs_path = stacks_root / "PACKS.json"
    packs = json.loads(packs_path.read_text(encoding="utf-8"))
    dewey_by_slug = {row["slug"]: row["dewey"] for row in packs}
    title_by_slug = {row["slug"]: row["title"] for row in packs}
    cards: list[dict] = []
    for facts in sorted(stacks_root.glob("*/FACTS.md")):
        slug = facts.parent.name
        dewey = dewey_by_slug.get(slug, "")
        title = title_by_slug.get(slug, slug)
        for lineno, raw in enumerate(facts.read_text(encoding="utf-8").splitlines(), start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            matched = LINE.match(line)
            if not matched:
                continue
            topic = matched.group("topic").strip()
            comment, door = _split_rest(matched.group("rest"))
            if len(comment) < 8:
                continue
            ident = f"{facts.as_posix()}:{lineno}:{topic}"
            cards.append(
                {
                    "card_id": hashlib.sha256(ident.encode("utf-8")).hexdigest(),
                    "kind": "stack",
                    "topic": topic,
                    "comment": comment,
                    "dewey": dewey,
                    "door": door,
                    "slug": slug,
                    "title": title,
                    "source": f"stacks/{slug}/FACTS.md:{lineno}",
                    "volatility": "pinned",
                }
            )
    return cards


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile EasyLM FACTS.md files into stack cards")
    parser.add_argument("stacks_root", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    cards = compile_stacks(args.stacks_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for card in cards:
            handle.write(json.dumps(card, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"{len(cards)} cards -> {args.out}")


if __name__ == "__main__":
    main()
