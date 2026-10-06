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

    # Sense lemmas
    cur.execute("SELECT lemma FROM nodes")
    sense_lemmas = {r[0] for r in cur.fetchall()}

    # Edges analysis
    cur.execute("SELECT source_id, target_id, source_lemma, target_lemma, relation FROM edges")
    edges = cur.fetchall()

    walkable = []
    quarantine = []
    self_loops = []
    dangling_targets = []
    null_target_ids = []

    for e in edges:
        s_id, t_id, s_lem, t_lem, rel = e
        is_self = (s_lem == t_lem)
        is_dangling = (t_lem not in sense_lemmas)
        is_null_id = (t_id is None)

        if is_self:
            self_loops.append(e)
            quarantine.append(e)
        elif is_dangling or is_null_id:
            if is_dangling:
                dangling_targets.append(e)
            if is_null_id:
                null_target_ids.append(e)
            quarantine.append(e)
        else:
            walkable.append(e)

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
    print(f"Walkable Edges:         {len(walkable)}")
    print(f"Quarantine Candidate:   {len(quarantine)}")
    print(f"  Self-loops:           {len(self_loops)}")
    print(f"  Dangling Targets:     {len(dangling_targets)}")
    print(f"  Null Target IDs:      {len(null_target_ids)}")
    print(f"Stub T1 Decompositions: {stub_t1_count}")
    print(f"Dewey 813.54 Outliers:  {dewey_813_count}")
    print(f"Short Glosses (<8 wds): {short_gloss_count}")

    con.close()
    return {
        "nodes": total_nodes,
        "edges": total_edges,
        "walkable": len(walkable),
        "quarantine": len(quarantine),
        "self_loops": len(self_loops),
        "dangling": len(dangling_targets),
        "stub_t1": stub_t1_count,
        "dewey_813": dewey_813_count,
        "short_gloss": short_gloss_count,
    }

if __name__ == "__main__":
    check_graph_gate()
