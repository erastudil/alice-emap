"""Resolve edge target_id against the sense nodes in emap.db."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_emap_graph import get_db, resolve_target_ids


def test_walkable_edges_have_both_ids():
    db = get_db()
    try:
        resolve_target_ids(db)
        cur = db.cursor()

        unresolved = cur.execute("""
            SELECT COUNT(*) FROM edges e
            WHERE EXISTS (SELECT 1 FROM nodes n WHERE n.lemma = e.target_lemma)
              AND e.target_id IS NULL
        """).fetchone()[0]
        assert unresolved == 0

        invented = cur.execute("""
            SELECT COUNT(*) FROM edges e
            WHERE e.target_id IS NOT NULL
              AND e.target_id != (
                  SELECT MIN(n.id) FROM nodes n WHERE n.lemma = e.target_lemma
              )
        """).fetchone()[0]
        assert invented == 0

        dangling = cur.execute("""
            SELECT COUNT(*) FROM edges e
            WHERE NOT EXISTS (SELECT 1 FROM nodes n WHERE n.lemma = e.target_lemma)
              AND e.target_id IS NOT NULL
        """).fetchone()[0]
        assert dangling == 0

        walkable_missing = cur.execute("""
            SELECT COUNT(*) FROM edges e
            WHERE e.source_lemma != e.target_lemma
              AND e.target_id IS NOT NULL
              AND e.source_id IS NULL
        """).fetchone()[0]
        assert walkable_missing == 0

        resolved = cur.execute(
            "SELECT COUNT(*) FROM edges WHERE target_id IS NOT NULL"
        ).fetchone()[0]
        walkable = cur.execute("""
            SELECT COUNT(*) FROM edges
            WHERE target_id IS NOT NULL AND source_lemma != target_lemma
        """).fetchone()[0]
        assert resolved == 6738
        assert walkable == 5390

        row = cur.execute("""
            SELECT target_id FROM edges
            WHERE source_lemma = 'a-long-time'
              AND target_lemma = 'a-short-time'
              AND relation = 'antonym'
        """).fetchone()
        sense = cur.execute(
            "SELECT id FROM nodes WHERE lemma = 'a-short-time'"
        ).fetchone()
        assert row[0] == sense[0]

        assert resolve_target_ids(db) == 0
    finally:
        db.close()
