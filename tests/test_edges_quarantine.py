"""Quarantine checks against the real emap.db.

Self-loops, targets with no sense, and sources with no sense leave `edges`.
A second pass moves nothing.
"""

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_emap_graph import quarantine_unwalkable_edges

DB_PATH = ROOT / "emap.db"
MEASURED_EDGES = 21195
SELF_LOOPS = 1353
DANGLING = 0
UNSENSED_SOURCE = 0
KEPT = 19842


def _connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def test_quarantine_is_idempotent_and_conserves_rows():
    db = _connect()
    try:
        first = quarantine_unwalkable_edges(db)
        second = quarantine_unwalkable_edges(db)
    finally:
        db.close()

    assert first["moved"] == 0
    assert first["deleted"] == 0
    assert second["moved"] == 0
    assert second["deleted"] == 0
    assert first["self_loop"] == SELF_LOOPS
    assert first["dangling"] == DANGLING
    assert first["unsensed_source"] == UNSENSED_SOURCE
    assert (
        first["self_loop"] + first["dangling"] + first["unsensed_source"] + KEPT
        == MEASURED_EDGES
    )


def test_edges_have_no_self_loops_or_dangling_targets():
    db = _connect()
    try:
        cur = db.cursor()
        edges = cur.execute("SELECT count(*) FROM edges").fetchone()[0]
        self_loops = cur.execute(
            "SELECT count(*) FROM edges WHERE source_lemma = target_lemma"
        ).fetchone()[0]
        dangling = cur.execute(
            """
            SELECT count(*) FROM edges e
            WHERE NOT EXISTS (SELECT 1 FROM nodes n WHERE n.lemma = e.target_lemma)
            """
        ).fetchone()[0]
        unsensed = cur.execute(
            """
            SELECT count(*) FROM edges e
            WHERE NOT EXISTS (SELECT 1 FROM nodes n WHERE n.lemma = e.source_lemma)
            """
        ).fetchone()[0]
        overlap = cur.execute(
            """
            SELECT count(*) FROM edges e
            JOIN edges_quarantine q
              ON e.source_lemma = q.source_lemma
             AND e.target_lemma = q.target_lemma
             AND e.relation = q.relation
            """
        ).fetchone()[0]
        bad_self = cur.execute(
            """
            SELECT count(*) FROM edges_quarantine
            WHERE reason = 'self_loop' AND source_lemma != target_lemma
            """
        ).fetchone()[0]
        bad_dangling = cur.execute(
            """
            SELECT count(*) FROM edges_quarantine q
            WHERE q.reason = 'dangling'
              AND (
                    q.source_lemma = q.target_lemma
                    OR EXISTS (SELECT 1 FROM nodes n WHERE n.lemma = q.target_lemma)
              )
            """
        ).fetchone()[0]
        bad_unsensed = cur.execute(
            """
            SELECT count(*) FROM edges_quarantine q
            WHERE q.reason = 'unsensed_source'
              AND (
                    q.source_lemma = q.target_lemma
                    OR NOT EXISTS (
                        SELECT 1 FROM nodes n WHERE n.lemma = q.target_lemma
                    )
                    OR EXISTS (
                        SELECT 1 FROM nodes n WHERE n.lemma = q.source_lemma
                    )
              )
            """
        ).fetchone()[0]
        sense_targets = cur.execute(
            """
            SELECT count(*) FROM edges e
            WHERE EXISTS (SELECT 1 FROM nodes n WHERE n.lemma = e.target_lemma)
            """
        ).fetchone()[0]
    finally:
        db.close()

    assert edges == KEPT
    assert self_loops == 0
    assert dangling == 0
    assert unsensed == 0
    assert overlap == 0
    assert bad_self == 0
    assert bad_dangling == 0
    assert bad_unsensed == 0
    assert sense_targets == edges
