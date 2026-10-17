"""test_syllogistic_map.py - Verification suite for Alice 1.0 English Syllogistic & Propositional Map."""

import json
import pathlib
import sqlite3
import pytest

from build_syllogistic_map import (
    MOOD_DEFINITIONS,
    PropositionalGraph,
    CategoricalPropositionEngine,
    SyllogisticInferenceEngine,
    SoritesChainSynthesizer,
    ConditionalRuleSynthesizer,
    SyllogisticOrchestrator,
    format_categorical_text,
    format_fol,
    format_truth_condition,
    clean_label
)

ROOT = pathlib.Path(__file__).resolve().parent.parent
EMAP_DB = ROOT / "emap.db"
SYL_DB = ROOT / "syllogistic_map.db"
SYL_JSONL = ROOT / "syllogisms.jsonl"


def _ensure_artifacts() -> None:
    if not SYL_DB.exists() or not SYL_JSONL.exists():
        SyllogisticOrchestrator(EMAP_DB, SYL_DB, SYL_JSONL).run_compilation()


def test_mood_definitions_count():
    assert len(MOOD_DEFINITIONS) == 24
    mood_names = [m[0] for m in MOOD_DEFINITIONS]
    expected_primary = [
        "Barbara", "Celarent", "Darii", "Ferio",
        "Cesare", "Camestres", "Festino", "Baroco",
        "Darapti", "Disamis", "Datisi", "Felapton", "Bocardo", "Ferison",
        "Bramantip", "Camenes", "Dimaris", "Fesapo", "Fresison"
    ]
    for mood in expected_primary:
        assert mood in mood_names, f"Primary mood {mood} missing from definitions"

    expected_subaltern = ["Barbari", "Celaront", "Cesaro", "Camestros", "Camenop"]
    for mood in expected_subaltern:
        assert mood in mood_names, f"Subaltern mood {mood} missing from definitions"


def test_categorical_proposition_formatting():
    assert format_categorical_text("dog", "mammal", "A") == "All dog are mammal."
    assert format_categorical_text("dog", "cat", "E") == "No dog are cat."
    assert format_categorical_text("animal", "dog", "I") == "Some animal are dog."
    assert format_categorical_text("animal", "dog", "O") == "Some animal are not dog."

    assert "∀x" in format_fol("dog", "mammal", "A")
    assert "→" in format_fol("dog", "mammal", "A")
    assert "¬" in format_fol("dog", "cat", "E")
    assert "∃x" in format_fol("animal", "dog", "I")
    assert "∧" in format_fol("animal", "dog", "I")

    assert "⊆" in format_truth_condition("dog", "mammal", "A")
    assert "∩" in format_truth_condition("dog", "cat", "E")
    assert "≠ ∅" in format_truth_condition("animal", "dog", "I")
    assert "\\" in format_truth_condition("animal", "dog", "O")


def test_graph_loading():
    graph = PropositionalGraph(EMAP_DB)
    conn = sqlite3.connect(str(EMAP_DB))
    senses = {
        row[0].strip().lower()
        for row in conn.execute("SELECT lemma FROM nodes")
        if row[0]
    }
    walkable = conn.execute(
        """
        SELECT count(*) FROM edges
        WHERE source_lemma != target_lemma
          AND length(source_lemma) > 1
          AND length(target_lemma) > 1
          AND source_lemma NOT LIKE '...%'
          AND target_lemma NOT LIKE '...%'
          AND target_id IS NOT NULL
          AND EXISTS (
              SELECT 1 FROM nodes n WHERE n.lemma = edges.source_lemma
          )
          AND EXISTS (
              SELECT 1 FROM nodes n WHERE n.lemma = edges.target_lemma
          )
        """
    ).fetchone()[0]
    quarantined = conn.execute("SELECT count(*) FROM edges_quarantine").fetchone()[0]
    conn.close()

    assert walkable > quarantined
    assert len(graph.edges) == walkable
    assert walkable > 19000
    for s, t, rel, w in graph.edges:
        assert s != t
        assert len(s) > 1
        assert len(t) > 1
        assert s in senses
        assert t in senses


def test_proposition_engine_compilation():
    graph = PropositionalGraph(EMAP_DB)
    prop_engine = CategoricalPropositionEngine(graph)
    prop_engine.compile()

    props = list(prop_engine.propositions.values())
    assert len(props) > 8000

    types = {p.prop_type for p in props}
    assert types == {"A", "E", "I", "O"}


def test_syllogism_derivation_all_moods():
    graph = PropositionalGraph(EMAP_DB)
    prop_engine = CategoricalPropositionEngine(graph)
    prop_engine.compile()

    syl_engine = SyllogisticInferenceEngine(prop_engine)
    syllogisms = syl_engine.derive(target_total=2400, max_per_mood=100)

    moods_found = {s.mood for s in syllogisms}
    assert len(moods_found) == 24
    for s in syllogisms:
        assert s.valid == 1
        assert s.subject_term != s.middle_term
        assert s.middle_term != s.predicate_term
        assert s.subject_term != s.predicate_term
        assert "Q.E.D." in s.symbolic_proof


def test_sorites_chain_synthesis():
    graph = PropositionalGraph(EMAP_DB)
    prop_engine = CategoricalPropositionEngine(graph)
    prop_engine.compile()

    sorites_engine = SoritesChainSynthesizer(prop_engine)
    chains = sorites_engine.synthesize(limit=100)

    assert len(chains) > 0
    for chain in chains:
        assert chain.chain_length >= 3
        assert len(chain.terms) == chain.chain_length + 1
        assert len(chain.premise_texts) == chain.chain_length
        assert "⊢" in chain.conditional_form
        assert "⟹" in chain.symbolic_chain


def test_conditional_rule_synthesis():
    graph = PropositionalGraph(EMAP_DB)
    prop_engine = CategoricalPropositionEngine(graph)
    prop_engine.compile()

    cond_engine = ConditionalRuleSynthesizer(prop_engine, graph)
    rules = cond_engine.generate(limit=1000)

    rule_types = {r.rule_type for r in rules}
    assert "implication" in rule_types
    assert "contrapositive" in rule_types
    assert "biconditional" in rule_types
    assert "modal_necessary" in rule_types
    assert "modal_impossible" in rule_types
    assert "modal_possible" in rule_types


def test_database_persistence_and_scale():
    _ensure_artifacts()
    assert SYL_DB.exists()
    conn = sqlite3.connect(str(SYL_DB))
    cur = conn.cursor()

    prop_count = cur.execute("SELECT count(*) FROM categorical_propositions").fetchone()[0]
    syl_count = cur.execute("SELECT count(*) FROM syllogisms").fetchone()[0]
    sorites_count = cur.execute("SELECT count(*) FROM sorites_chains").fetchone()[0]
    rules_count = cur.execute("SELECT count(*) FROM conditional_rules").fetchone()[0]

    assert prop_count >= 8000, f"Propositions count {prop_count} < 8000"
    assert syl_count >= 10000, f"Syllogisms count {syl_count} < 10000"
    assert sorites_count >= 1000, f"Sorites count {sorites_count} < 1000"
    assert rules_count >= 5000, f"Rules count {rules_count} < 5000"

    distinct_moods = cur.execute("SELECT count(DISTINCT mood) FROM syllogisms").fetchone()[0]
    assert distinct_moods == 24, f"Moods count {distinct_moods} < 24"

    conn.close()


def test_jsonl_validity():
    _ensure_artifacts()
    assert SYL_JSONL.exists()
    line_count = 0
    with open(str(SYL_JSONL), "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            assert "unit_type" in data
            assert "id" in data
            line_count += 1
            if line_count > 500:
                break
    assert line_count > 500
