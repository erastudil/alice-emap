"""CSR export keeps a missing target off node index 0."""

import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_emap_graph import export_csr, get_db


def _insert_node(db, node_id: int, lemma: str) -> None:
    db.execute(
        """
        INSERT INTO nodes (
            id, lemma, pos, tier, sense_id, gloss, dewey,
            t1_decomposition, depth, lorentz_r
        ) VALUES (?, ?, 'N', 0, ?, 'a short gloss for the test', '001', 'THING(x)', 1, 0.0)
        """,
        (node_id, lemma, f"sense-{lemma}"),
    )


def test_missing_target_is_omitted(tmp_path: Path):
    db = get_db(tmp_path / "emap.db")
    try:
        _insert_node(db, 0, "zeta")
        _insert_node(db, 5, "water")
        db.executemany(
            """
            INSERT INTO edges (source_id, target_id, relation, weight, source_lemma, target_lemma)
            VALUES (5, NULL, 'hypernym', 0.9, ?, ?)
            """,
            [("water", "not-a-lemma"), ("water", "zeta")],
        )
        db.commit()

        out_bin = tmp_path / "emap_csr.bin"
        out_meta = tmp_path / "emap_csr.json"
        export_csr(db, out_bin=out_bin, out_meta=out_meta)
    finally:
        db.close()

    magic, version, n_nodes, n_edges = struct.unpack("<4sIII", out_bin.read_bytes()[:16])
    assert magic == b"EMAP"
    assert version == 1
    assert n_nodes == 2
    assert n_edges == 1

    indptr = struct.unpack("<3i", out_bin.read_bytes()[16:28])
    indices = struct.unpack("<1i", out_bin.read_bytes()[28:32])
    assert indptr == (0, 0, 1)
    assert indices == (0,)


def test_shared_lemma_does_not_share_a_slot(tmp_path: Path):
    db = get_db(tmp_path / "emap.db")
    try:
        _insert_node(db, 10, "alpha")
        db.executemany(
            """
            INSERT INTO nodes (
                id, lemma, pos, tier, sense_id, gloss, dewey,
                t1_decomposition, depth, lorentz_r
            ) VALUES (?, 'torment', ?, 0, ?, 'a short gloss for the test', '001', 'THING(x)', 1, 0.0)
            """,
            [(20, "N", "torment.n.01"), (30, "V", "torment.v.01")],
        )
        db.executemany(
            """
            INSERT INTO edges (source_id, target_id, relation, weight, source_lemma, target_lemma)
            VALUES (?, ?, ?, 0.9, ?, ?)
            """,
            [
                (20, 10, "hypernym", "torment", "alpha"),
                (10, None, "hyponym", "alpha", "torment"),
            ],
        )
        db.commit()

        out_bin = tmp_path / "emap_csr.bin"
        out_meta = tmp_path / "emap_csr.json"
        export_csr(db, out_bin=out_bin, out_meta=out_meta)
    finally:
        db.close()

    _magic, _version, n_nodes, n_edges = struct.unpack("<4sIII", out_bin.read_bytes()[:16])
    assert n_nodes == 3
    assert n_edges == 2
    # id order: alpha, noun torment, verb torment
    indptr = struct.unpack("<4i", out_bin.read_bytes()[16:32])
    indices = struct.unpack("<2i", out_bin.read_bytes()[32:40])
    assert indptr == (0, 1, 2, 2)
    assert indices == (1, 0)

class TestExportCsr(unittest.TestCase):
    def test_missing_target_is_omitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            test_missing_target_is_omitted(Path(tmp))


if __name__ == "__main__":
    unittest.main()
