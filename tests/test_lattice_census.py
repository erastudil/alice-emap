"""The contract names the lattice stored in emap.db and emap_csr.json."""

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _census() -> dict:
    db = sqlite3.connect(ROOT / "emap.db")
    try:
        lemmas = db.execute("SELECT count(*) FROM lemmas").fetchone()[0]
        nodes = db.execute("SELECT count(*) FROM nodes").fetchone()[0]
        edges = db.execute("SELECT count(*) FROM edges").fetchone()[0]
        self_loops = db.execute(
            "SELECT count(*) FROM edges_quarantine WHERE reason = 'self_loop'"
        ).fetchone()[0]
        dangling = db.execute(
            "SELECT count(*) FROM edges_quarantine WHERE reason = 'dangling'"
        ).fetchone()[0]
        unsensed = db.execute(
            "SELECT count(*) FROM edges_quarantine WHERE reason = 'unsensed_source'"
        ).fetchone()[0]
    finally:
        db.close()
    meta = json.loads((ROOT / "emap_csr.json").read_text(encoding="utf-8"))
    return {
        "lemmas": lemmas,
        "nodes": nodes,
        "edges": edges,
        "self_loops": self_loops,
        "dangling": dangling,
        "unsensed": unsensed,
        "meta": meta,
    }


def test_csr_matches_the_walkable_table():
    census = _census()
    meta = census["meta"]
    assert meta["node_count"] == census["nodes"]
    assert meta["edge_count"] == census["edges"]
    assert (ROOT / "emap_csr.bin").stat().st_size == meta["payload_bytes"]
    assert census["dangling"] == 0
    assert census["unsensed"] == 0


def test_contract_names_the_measured_lattice():
    census = _census()
    lemmas = census["lemmas"]
    nodes = census["nodes"]
    edges = census["edges"]
    self_loops = census["self_loops"]
    payload = census["meta"]["payload_bytes"]

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"{lemmas} lemmas and {nodes} sense nodes" in readme
    assert f"The {self_loops} self-loops sit in `edges_quarantine`" in readme
    assert f"The {edges} walkable edges" in readme

    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert f"{lemmas} lemmas and {nodes} sense nodes" in agents

    spec = (ROOT / "SPEC.md").read_text(encoding="utf-8")
    assert f"`lemmas` {lemmas}, `nodes` {nodes}" in spec
    assert f"`edges` holds {edges} walkable rows" in spec
    assert f"{self_loops} `self_loop`" in spec
    assert f"payload {payload} bytes, {nodes} nodes, {edges} edges" in spec

    card = (ROOT / "tools" / "upload_alice_adapter.py").read_text(encoding="utf-8")
    assert f"{lemmas} lemmas, {nodes} sense nodes, {edges} CSR edges" in card
