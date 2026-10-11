"""tools/graph_gate.py - Graph Gate and Acceptance Metrics for Alice EMap."""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "emap.db"

STUB_T1 = {
    "NAME(x)", "PERSON(x)", "LOCATION(x)", "NOUN(x)",
    "ADJECTIVE(x)", "ACTION(x)", "PRED(x)", "SUBSTANCE(x)", "VERB(x)"
}

def check_graph_gate():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    total_nodes = cur.execute("SELECT count(*) FROM nodes").fetchone()[0]
    total_edges = cur.execute("SELECT count(*) FROM edges").fetchone()[0]

    has_quarantine = cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'edges_quarantine'"
    ).fetchone() is not None
    if has_quarantine:
        quarantine_count = cur.execute("SELECT count(*) FROM edges_quarantine").fetchone()[0]
        quarantined_self = cur.execute(
            "SELECT count(*) FROM edges_quarantine WHERE reason = 'self_loop'"
        ).fetchone()[0]
        quarantined_dangling = cur.execute(
            "SELECT count(*) FROM edges_quarantine WHERE reason = 'dangling'"
        ).fetchone()[0]
    else:
        quarantine_count = 0
        quarantined_self = 0
        quarantined_dangling = 0

    residual_self = cur.execute(
        "SELECT count(*) FROM edges WHERE source_lemma = target_lemma"
    ).fetchone()[0]
    residual_dangling = cur.execute(
        """
        SELECT count(*) FROM edges e
        WHERE NOT EXISTS (SELECT 1 FROM nodes n WHERE n.lemma = e.target_lemma)
        """
    ).fetchone()[0]
    null_target_ids = cur.execute(
        "SELECT count(*) FROM edges WHERE target_id IS NULL"
    ).fetchone()[0]
    walkable_count = cur.execute(
        """
        SELECT count(*) FROM edges e
        WHERE e.target_id IS NOT NULL
          AND e.source_lemma != e.target_lemma
          AND EXISTS (SELECT 1 FROM nodes n WHERE n.lemma = e.target_lemma)
        """
    ).fetchone()[0]

    # Node metrics
    cur.execute("SELECT id, lemma, dewey, t1_decomposition, gloss FROM nodes")
    node_rows = cur.fetchall()

    stub_t1_count = 0
    dewey_813_count = 0
    short_gloss_count = 0

    for _, _, dewey, t1, gloss in node_rows:
        if t1 in STUB_T1:
            stub_t1_count += 1
        if dewey == "813.54":
            dewey_813_count += 1
        if not gloss or len(gloss.split()) < 8:
            short_gloss_count += 1

    print("=== Alice EMap Graph Gate ===")
    print(f"Total Nodes:            {total_nodes}")
    print(f"Total Edges:            {total_edges}")
    print(f"Walkable Edges:         {walkable_count}")
    print(f"Quarantine:             {quarantine_count}")
    print(f"  Self-loops:           {quarantined_self}")
    print(f"  Dangling Targets:     {quarantined_dangling}")
    print(f"  Residual Self-loops:  {residual_self}")
    print(f"  Residual Dangling:    {residual_dangling}")
    print(f"  Null Target IDs:      {null_target_ids}")
    print(f"Stub T1 Decompositions: {stub_t1_count}")
    print(f"Dewey 813.54 Outliers:  {dewey_813_count}")
    print(f"Short Glosses (<8 wds): {short_gloss_count}")

    con.close()
    return {
        "nodes": total_nodes,
        "edges": total_edges,
        "walkable": walkable_count,
        "quarantine": quarantine_count,
        "self_loops": quarantined_self,
        "dangling": quarantined_dangling,
        "residual_self": residual_self,
        "residual_dangling": residual_dangling,
        "stub_t1": stub_t1_count,
        "dewey_813": dewey_813_count,
        "short_gloss": short_gloss_count,
    }

if __name__ == "__main__":
    check_graph_gate()
