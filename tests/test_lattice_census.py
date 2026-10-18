"""The shipped CSR, the walkable table, and the contract cite one lattice."""

import json
import sqlite3
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "emap.db"
CSR_JSON = ROOT / "emap_csr.json"
CSR_BIN = ROOT / "emap_csr.bin"


def _measured():
    db = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        cur = db.cursor()
        lemmas = cur.execute("SELECT count(*) FROM lemmas").fetchone()[0]
        nodes = cur.execute("SELECT count(*) FROM nodes").fetchone()[0]
        edges = cur.execute("SELECT count(*) FROM edges").fetchone()[0]
        self_loops = cur.execute(
            "SELECT count(*) FROM edges_quarantine WHERE reason = 'self_loop'"
        ).fetchone()[0]
        kernel = cur.execute(
            "SELECT count(*) FROM lemmas WHERE is_kernel = 1"
        ).fetchone()[0]
    finally:
        db.close()
    meta = json.loads(CSR_JSON.read_text(encoding="utf-8"))
    magic, version, n_nodes, n_edges = struct.unpack("<4sIII", CSR_BIN.read_bytes()[:16])
    return {
        "lemmas": lemmas,
        "nodes": nodes,
        "edges": edges,
        "self_loops": self_loops,
        "kernel": kernel,
        "meta": meta,
        "magic": magic,
        "version": version,
        "n_nodes": n_nodes,
        "n_edges": n_edges,
        "payload": CSR_BIN.stat().st_size,
    }


def test_shipped_csr_matches_walkable_tables():
    measured = _measured()
    meta = measured["meta"]
    assert measured["magic"] == b"EMAP"
    assert measured["version"] == 1
    assert meta["node_count"] == measured["n_nodes"] == measured["nodes"]
    assert meta["edge_count"] == measured["n_edges"] == measured["edges"]
    assert meta["payload_bytes"] == measured["payload"]


def test_contract_cites_measured_lattice():
    measured = _measured()
    lemmas = measured["lemmas"]
    nodes = measured["nodes"]
    edges = measured["edges"]
    self_loops = measured["self_loops"]
    kernel = measured["kernel"]
    payload = measured["payload"]

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    spec = (ROOT / "SPEC.md").read_text(encoding="utf-8")
    card = (ROOT / "tools" / "upload_alice_adapter.py").read_text(encoding="utf-8")

    assert f"{lemmas} lemmas and {nodes} sense nodes" in readme
    assert f"{edges} walkable edges" in readme
    assert f"{self_loops} self-loops" in readme
    assert f"{lemmas} lemmas and {nodes} sense nodes" in agents
    assert f"Lemmas {lemmas}." in spec
    assert f"Sense nodes {nodes}." in spec
    assert f"Walkable edges {edges}." in spec
    assert f"Kernel flag {kernel}." in spec
    assert f"payload {payload} bytes" in spec
    assert f"{self_loops} self-loops" in spec
    assert (
        f"{lemmas:,} lemmas, {nodes:,} sense nodes, {edges:,} CSR edges" in card
    )
