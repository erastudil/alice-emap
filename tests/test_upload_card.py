"""The adapter card cites the graph files it bundles."""

import importlib.util
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_spec = importlib.util.spec_from_file_location(
    "upload_alice_adapter",
    ROOT / "tools" / "upload_alice_adapter.py",
)
upload = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(upload)


def test_model_card_cites_the_measured_csr():
    topology = upload.measured_topology(ROOT)
    card = upload.model_card(topology)

    csr = json.loads((ROOT / "emap_csr.json").read_text(encoding="utf-8"))
    with sqlite3.connect(ROOT / "emap.db") as con:
        lemmas = con.execute("SELECT count(*) FROM lemmas").fetchone()[0]

    assert topology["lemmas"] == lemmas
    assert topology["sense_nodes"] == csr["node_count"]
    assert topology["csr_edges"] == csr["edge_count"]
    assert f"{lemmas:,} lemmas" in card
    assert f"{csr['node_count']:,} sense nodes" in card
    assert f"{csr['edge_count']:,} CSR edges" in card
    assert "21,169" not in card
    assert "{ header, offset }" in card
