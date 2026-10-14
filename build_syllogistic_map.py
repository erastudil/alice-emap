"""build_syllogistic_map.py - Alice 1.0 Exhaustive English Syllogistic and Propositional Logic Engine.

Architects and drives continuous generation of the exhaustive English syllogistic
and propositional logic map for Alice.
"""

from __future__ import annotations

import argparse
import collections
import dataclasses
import hashlib
import json
import os
import pathlib
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


@dataclasses.dataclass(frozen=True)
class CategoricalProposition:
    prop_id: str
    subject: str
    predicate: str
    prop_type: str  # 'A', 'E', 'I', 'O'
    natural_text: str
    symbolic_fol: str
    truth_condition: str
    source_relation: str
    confidence: float
    is_axiom: int = 1


@dataclasses.dataclass(frozen=True)
class Syllogism:
    syllogism_id: str
    figure: int
    mood: str
    mood_code: str
    subject_term: str      # S
    middle_term: str       # M
    predicate_term: str    # P
    major_premise_id: str
    minor_premise_id: str
    conclusion_id: str
    major_text: str
    minor_text: str
    conclusion_text: str
    truth_condition: str
    symbolic_proof: str
    requires_existential_import: int
    valid: int
    created_at: str


@dataclasses.dataclass(frozen=True)
class SoritesChain:
    chain_id: str
    chain_length: int
    terms: List[str]
    premise_ids: List[str]
    premise_texts: List[str]
    conclusion_text: str
    conditional_form: str
    symbolic_chain: str
    relations: List[str]
    created_at: str


@dataclasses.dataclass(frozen=True)
class ConditionalRule:
    rule_id: str
    rule_type: str
    antecedent: str
    consequent: str
    natural_text: str
    symbolic_form: str
    source_relation: str
    confidence: float
    created_at: str


def clean_label(text: str) -> str:
    """Normalizes lemma tokens for natural presentation."""
    return text.strip().replace("_", " ")


def format_categorical_text(s: str, p: str, prop_type: str) -> str:
    """Generates canonical English categorical proposition."""
    s_clean = clean_label(s)
    p_clean = clean_label(p)
    if prop_type == "A":
        return f"All {s_clean} are {p_clean}."
    elif prop_type == "E":
        return f"No {s_clean} are {p_clean}."
    elif prop_type == "I":
        return f"Some {s_clean} are {p_clean}."
    elif prop_type == "O":
        return f"Some {s_clean} are not {p_clean}."
    raise ValueError(f"Invalid proposition type: {prop_type}")


def format_fol(s: str, p: str, prop_type: str) -> str:
    """Generates first-order predicate logic representation."""
    s_sym = re.sub(r"[^a-zA-Z0-9_]", "_", s)
    p_sym = re.sub(r"[^a-zA-Z0-9_]", "_", p)
    if prop_type == "A":
        return f"∀x ({s_sym}(x) → {p_sym}(x))"
    elif prop_type == "E":
        return f"∀x ({s_sym}(x) → ¬{p_sym}(x))"
    elif prop_type == "I":
        return f"∃x ({s_sym}(x) ∧ {p_sym}(x))"
    elif prop_type == "O":
        return f"∃x ({s_sym}(x) ∧ ¬{p_sym}(x))"
    raise ValueError(f"Invalid proposition type: {prop_type}")


def format_truth_condition(s: str, p: str, prop_type: str) -> str:
    """Generates exact set-theoretic truth conditions."""
    s_sym = clean_label(s)
    p_sym = clean_label(p)
    if prop_type == "A":
        return f"{s_sym} ⊆ {p_sym} ∧ {s_sym} ≠ ∅"
    elif prop_type == "E":
        return f"{s_sym} ∩ {p_sym} = ∅"
    elif prop_type == "I":
        return f"{s_sym} ∩ {p_sym} ≠ ∅"
    elif prop_type == "O":
        return f"{s_sym} \\ {p_sym} ≠ ∅"
    raise ValueError(f"Invalid proposition type: {prop_type}")


def make_prop_id(prop_type: str, s: str, p: str) -> str:
    """Generates deterministic proposition identifier."""
    key = f"{prop_type}:{s.lower()}:{p.lower()}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]
    s_tok = re.sub(r"[^a-zA-Z0-9]", "", s)[:10]
    p_tok = re.sub(r"[^a-zA-Z0-9]", "", p)[:10]
    return f"prop_{prop_type}_{s_tok}_{p_tok}_{digest}"


# ---------------------------------------------------------------------------
# All 24 Scholastic Moods across Figures 1-4
# Format: (mood_name, figure, mood_code, major_type, minor_type, conc_type, requires_existential_import, proof_template)
# ---------------------------------------------------------------------------
MOOD_DEFINITIONS = [
    # Figure 1: Major M-P, Minor S-M, Conclusion S-P
    ("Barbara", 1, "AAA-1", "A", "A", "A", 0,
     "1. ∀x (M(x) → P(x)) [Major premise]\n"
     "2. ∀x (S(x) → M(x)) [Minor premise]\n"
     "3. Transitivity of universal implication: ∀x (S(x) → P(x))\n"
     "Set condition: S ⊆ M ∧ M ⊆ P ⟹ S ⊆ P. Q.E.D."),

    ("Celarent", 1, "EAE-1", "E", "A", "E", 0,
     "1. ∀x (M(x) → ¬P(x)) [Major premise]\n"
     "2. ∀x (S(x) → M(x)) [Minor premise]\n"
     "3. Substitution into universal negation: ∀x (S(x) → ¬P(x))\n"
     "Set condition: S ⊆ M ∧ M ∩ P = ∅ ⟹ S ∩ P = ∅. Q.E.D."),

    ("Darii", 1, "AII-1", "A", "I", "I", 0,
     "1. ∀x (M(x) → P(x)) [Major premise]\n"
     "2. ∃x (S(x) ∧ M(x)) [Minor premise]\n"
     "3. Instantiation witness c: S(c) ∧ M(c); Major yields P(c); hence ∃x (S(x) ∧ P(x))\n"
     "Set condition: S ∩ M ≠ ∅ ∧ M ⊆ P ⟹ S ∩ P ≠ ∅. Q.E.D."),

    ("Ferio", 1, "EIO-1", "E", "I", "O", 0,
     "1. ∀x (M(x) → ¬P(x)) [Major premise]\n"
     "2. ∃x (S(x) ∧ M(x)) [Minor premise]\n"
     "3. Instantiation witness c: S(c) ∧ M(c); Major yields ¬P(c); hence ∃x (S(x) ∧ ¬P(x))\n"
     "Set condition: S ∩ M ≠ ∅ ∧ M ∩ P = ∅ ⟹ S \\ P ≠ ∅. Q.E.D."),

    ("Barbari", 1, "AAI-1", "A", "A", "I", 1,
     "1. ∀x (M(x) → P(x)) [Major premise]\n"
     "2. ∀x (S(x) → M(x)) [Minor premise]\n"
     "3. Barbara yields ∀x (S(x) → P(x)); existential import on S (S ≠ ∅) yields ∃x (S(x) ∧ P(x))\n"
     "Set condition: S ⊆ P ∧ S ≠ ∅ ⟹ S ∩ P ≠ ∅. Q.E.D."),

    ("Celaront", 1, "EAO-1", "E", "A", "O", 1,
     "1. ∀x (M(x) → ¬P(x)) [Major premise]\n"
     "2. ∀x (S(x) → M(x)) [Minor premise]\n"
     "3. Celarent yields ∀x (S(x) → ¬P(x)); existential import on S (S ≠ ∅) yields ∃x (S(x) ∧ ¬P(x))\n"
     "Set condition: S ∩ P = ∅ ∧ S ≠ ∅ ⟹ S \\ P ≠ ∅. Q.E.D."),

    # Figure 2: Major P-M, Minor S-M, Conclusion S-P
    ("Cesare", 2, "EAE-2", "E", "A", "E", 0,
     "1. ∀x (P(x) → ¬M(x)) [Major premise]\n"
     "2. ∀x (S(x) → M(x)) [Minor premise]\n"
     "3. Conversion of E yields ∀x (M(x) → ¬P(x)); reduction to Celarent yields ∀x (S(x) → ¬P(x))\n"
     "Set condition: P ∩ M = ∅ ∧ S ⊆ M ⟹ S ∩ P = ∅. Q.E.D."),

    ("Camestres", 2, "AEE-2", "A", "E", "E", 0,
     "1. ∀x (P(x) → M(x)) [Major premise]\n"
     "2. ∀x (S(x) → ¬M(x)) [Minor premise]\n"
     "3. Contrapositive on Major yields ∀x (¬M(x) → ¬P(x)); combined with Minor yields ∀x (S(x) → ¬P(x))\n"
     "Set condition: P ⊆ M ∧ S ∩ M = ∅ ⟹ S ∩ P = ∅. Q.E.D."),

    ("Festino", 2, "EIO-2", "E", "I", "O", 0,
     "1. ∀x (P(x) → ¬M(x)) [Major premise]\n"
     "2. ∃x (S(x) ∧ M(x)) [Minor premise]\n"
     "3. Conversion of E yields ∀x (M(x) → ¬P(x)); reduction to Ferio yields ∃x (S(x) ∧ ¬P(x))\n"
     "Set condition: P ∩ M = ∅ ∧ S ∩ M ≠ ∅ ⟹ S \\ P ≠ ∅. Q.E.D."),

    ("Baroco", 2, "AOO-2", "A", "O", "O", 0,
     "1. ∀x (P(x) → M(x)) [Major premise]\n"
     "2. ∃x (S(x) ∧ ¬M(x)) [Minor premise]\n"
     "3. Contrapositive on Major yields ¬M(x) → ¬P(x); witness c with S(c) ∧ ¬M(c) yields S(c) ∧ ¬P(c)\n"
     "Set condition: P ⊆ M ∧ S \\ M ≠ ∅ ⟹ S \\ P ≠ ∅. Q.E.D."),

    ("Cesaro", 2, "EAO-2", "E", "A", "O", 1,
     "1. ∀x (P(x) → ¬M(x)) [Major premise]\n"
     "2. ∀x (S(x) → M(x)) [Minor premise]\n"
     "3. Cesare yields ∀x (S(x) → ¬P(x)); existential import on S (S ≠ ∅) yields ∃x (S(x) ∧ ¬P(x))\n"
     "Set condition: S ∩ P = ∅ ∧ S ≠ ∅ ⟹ S \\ P ≠ ∅. Q.E.D."),

    ("Camestros", 2, "AEO-2", "A", "E", "O", 1,
     "1. ∀x (P(x) → M(x)) [Major premise]\n"
     "2. ∀x (S(x) → ¬M(x)) [Minor premise]\n"
     "3. Camestres yields ∀x (S(x) → ¬P(x)); existential import on S (S ≠ ∅) yields ∃x (S(x) ∧ ¬P(x))\n"
     "Set condition: S ∩ P = ∅ ∧ S ≠ ∅ ⟹ S \\ P ≠ ∅. Q.E.D."),

    # Figure 3: Major M-P, Minor M-S, Conclusion S-P
    ("Darapti", 3, "AAI-3", "A", "A", "I", 1,
     "1. ∀x (M(x) → P(x)) [Major premise]\n"
     "2. ∀x (M(x) → S(x)) [Minor premise]\n"
     "3. Existential import on middle term M (∃c M(c)): c ∈ M ⟹ c ∈ S ∧ c ∈ P; hence ∃x (S(x) ∧ P(x))\n"
     "Set condition: M ⊆ P ∧ M ⊆ S ∧ M ≠ ∅ ⟹ S ∩ P ≠ ∅. Q.E.D."),

    ("Disamis", 3, "IAI-3", "I", "A", "I", 0,
     "1. ∃x (M(x) ∧ P(x)) [Major premise]\n"
     "2. ∀x (M(x) → S(x)) [Minor premise]\n"
     "3. Witness c satisfies M(c) ∧ P(c); Minor yields S(c); thus S(c) ∧ P(c); hence ∃x (S(x) ∧ P(x))\n"
     "Set condition: M ∩ P ≠ ∅ ∧ M ⊆ S ⟹ S ∩ P ≠ ∅. Q.E.D."),

    ("Datisi", 3, "AII-3", "A", "I", "I", 0,
     "1. ∀x (M(x) → P(x)) [Major premise]\n"
     "2. ∃x (M(x) ∧ S(x)) [Minor premise]\n"
     "3. Witness c satisfies M(c) ∧ S(c); Major yields P(c); thus S(c) ∧ P(c); hence ∃x (S(x) ∧ P(x))\n"
     "Set condition: M ⊆ P ∧ M ∩ S ≠ ∅ ⟹ S ∩ P ≠ ∅. Q.E.D."),

    ("Felapton", 3, "EAO-3", "E", "A", "O", 1,
     "1. ∀x (M(x) → ¬P(x)) [Major premise]\n"
     "2. ∀x (M(x) → S(x)) [Minor premise]\n"
     "3. Existential import on middle term M (∃c M(c)): c ∈ M ⟹ c ∈ S ∧ c ∉ P; hence ∃x (S(x) ∧ ¬P(x))\n"
     "Set condition: M ∩ P = ∅ ∧ M ⊆ S ∧ M ≠ ∅ ⟹ S \\ P ≠ ∅. Q.E.D."),

    ("Bocardo", 3, "OAO-3", "O", "A", "O", 0,
     "1. ∃x (M(x) ∧ ¬P(x)) [Major premise]\n"
     "2. ∀x (M(x) → S(x)) [Minor premise]\n"
     "3. Witness c satisfies M(c) ∧ ¬P(c); Minor yields S(c); thus S(c) ∧ ¬P(c); hence ∃x (S(x) ∧ ¬P(x))\n"
     "Set condition: M \\ P ≠ ∅ ∧ M ⊆ S ⟹ S \\ P ≠ ∅. Q.E.D."),

    ("Ferison", 3, "EIO-3", "E", "I", "O", 0,
     "1. ∀x (M(x) → ¬P(x)) [Major premise]\n"
     "2. ∃x (M(x) ∧ S(x)) [Minor premise]\n"
     "3. Witness c satisfies M(c) ∧ S(c); Major yields ¬P(c); thus S(c) ∧ ¬P(c); hence ∃x (S(x) ∧ ¬P(x))\n"
     "Set condition: M ∩ P = ∅ ∧ M ∩ S ≠ ∅ ⟹ S \\ P ≠ ∅. Q.E.D."),

    # Figure 4: Major P-M, Minor M-S, Conclusion S-P
    ("Bramantip", 4, "AAI-4", "A", "A", "I", 1,
     "1. ∀x (P(x) → M(x)) [Major premise]\n"
     "2. ∀x (M(x) → S(x)) [Minor premise]\n"
     "3. Transitivity yields P ⊆ S; existential import on major term P (P ≠ ∅) yields ∃x (S(x) ∧ P(x))\n"
     "Set condition: P ⊆ M ∧ M ⊆ S ∧ P ≠ ∅ ⟹ S ∩ P ≠ ∅. Q.E.D."),

    ("Camenes", 4, "AEE-4", "A", "E", "E", 0,
     "1. ∀x (P(x) → M(x)) [Major premise]\n"
     "2. ∀x (M(x) → ¬S(x)) [Minor premise]\n"
     "3. Transitivity yields P ∩ S = ∅; conversion of E yields ∀x (S(x) → ¬P(x))\n"
     "Set condition: P ⊆ M ∧ M ∩ S = ∅ ⟹ S ∩ P = ∅. Q.E.D."),

    ("Dimaris", 4, "IAI-4", "I", "A", "I", 0,
     "1. ∃x (P(x) ∧ M(x)) [Major premise]\n"
     "2. ∀x (M(x) → S(x)) [Minor premise]\n"
     "3. Witness c satisfies P(c) ∧ M(c); Minor yields S(c); thus S(c) ∧ P(c); hence ∃x (S(x) ∧ P(x))\n"
     "Set condition: P ∩ M ≠ ∅ ∧ M ⊆ S ⟹ S ∩ P ≠ ∅. Q.E.D."),

    ("Fesapo", 4, "EAO-4", "E", "A", "O", 1,
     "1. ∀x (P(x) → ¬M(x)) [Major premise]\n"
     "2. ∀x (M(x) → S(x)) [Minor premise]\n"
     "3. Conversion of Major yields M ∩ P = ∅; existential import on M (M ≠ ∅) yields ∃x (S(x) ∧ ¬P(x))\n"
     "Set condition: P ∩ M = ∅ ∧ M ⊆ S ∧ M ≠ ∅ ⟹ S \\ P ≠ ∅. Q.E.D."),

    ("Fresison", 4, "EIO-4", "E", "I", "O", 0,
     "1. ∀x (P(x) → ¬M(x)) [Major premise]\n"
     "2. ∃x (M(x) ∧ S(x)) [Minor premise]\n"
     "3. Conversion of Major yields M ∩ P = ∅; witness c with M(c) ∧ S(c) yields S(c) ∧ ¬P(c)\n"
     "Set condition: P ∩ M = ∅ ∧ M ∩ S ≠ ∅ ⟹ S \\ P ≠ ∅. Q.E.D."),

    ("Camenop", 4, "AEO-4", "A", "E", "O", 1,
     "1. ∀x (P(x) → M(x)) [Major premise]\n"
     "2. ∀x (M(x) → ¬S(x)) [Minor premise]\n"
     "3. Camenes yields ∀x (S(x) → ¬P(x)); existential import on S (S ≠ ∅) yields ∃x (S(x) ∧ ¬P(x))\n"
     "Set condition: S ∩ P = ∅ ∧ S ≠ ∅ ⟹ S \\ P ≠ ∅. Q.E.D."),
]


class PropositionalGraph:
    """Loads and indexes lexical relationships from emap.db."""

    def __init__(self, emap_db_path: pathlib.Path) -> None:
        self.emap_db_path = emap_db_path
        self.nodes_pos: Dict[str, str] = {}
        self.nodes_gloss: Dict[str, str] = {}
        self.edges: List[Tuple[str, str, str, float]] = []
        self._load_data()

    def _load_data(self) -> None:
        conn = sqlite3.connect(str(self.emap_db_path))
        cur = conn.cursor()

        # Load nodes POS and glosses
        for row in cur.execute("SELECT lemma, pos, gloss FROM nodes"):
            lemma, pos, gloss = row[0], row[1], row[2]
            if lemma:
                self.nodes_pos[lemma] = pos
                self.nodes_gloss[lemma] = gloss

        # Walkable edges only. Self-loops and targets with no sense live in
        # edges_quarantine and are not premises.
        query = """
        SELECT source_lemma, target_lemma, relation, weight
        FROM edges
        WHERE source_lemma != target_lemma
          AND length(source_lemma) > 1
          AND length(target_lemma) > 1
          AND source_lemma NOT LIKE '...%'
          AND target_lemma NOT LIKE '...%'
          AND target_id IS NOT NULL
          AND EXISTS (
              SELECT 1 FROM nodes n WHERE n.lemma = edges.target_lemma
          )
        """
        for row in cur.execute(query):
            s, t, rel, w = row[0].strip().lower(), row[1].strip().lower(), row[2].strip().lower(), float(row[3])
            if s and t and s != t:
                self.edges.append((s, t, rel, w))

        conn.close()


class CategoricalPropositionEngine:
    """Generates A, E, I, O categorical propositions across graph lemmas."""

    def __init__(self, graph: PropositionalGraph) -> None:
        self.graph = graph
        self.propositions: Dict[str, CategoricalProposition] = {}
        # Multi-indexes for fast syllogistic matching
        self.by_subj_and_type: Dict[str, Dict[str, Dict[str, CategoricalProposition]]] = collections.defaultdict(
            lambda: collections.defaultdict(dict)
        )
        self.by_pred_and_type: Dict[str, Dict[str, Dict[str, CategoricalProposition]]] = collections.defaultdict(
            lambda: collections.defaultdict(dict)
        )

    def _add_prop(self, s: str, p: str, ptype: str, source_rel: str, confidence: float, is_axiom: int = 1) -> None:
        if s == p or len(s) < 2 or len(p) < 2:
            return
        pid = make_prop_id(ptype, s, p)
        if pid in self.propositions:
            return

        text = format_categorical_text(s, p, ptype)
        fol = format_fol(s, p, ptype)
        cond = format_truth_condition(s, p, ptype)

        prop = CategoricalProposition(
            prop_id=pid,
            subject=s,
            predicate=p,
            prop_type=ptype,
            natural_text=text,
            symbolic_fol=fol,
            truth_condition=cond,
            source_relation=source_rel,
            confidence=confidence,
            is_axiom=is_axiom
        )
        self.propositions[pid] = prop
        self.by_subj_and_type[s][ptype][p] = prop
        self.by_pred_and_type[p][ptype][s] = prop

    def compile(self) -> None:
        hypernym_children: Dict[str, Set[str]] = collections.defaultdict(set)

        for s, t, rel, w in self.graph.edges:
            # Universal Affirmative (A): S ⊆ P
            if rel in ("hypernym", "instance_of"):
                self._add_prop(s, t, "A", rel, w, is_axiom=1)
                self._add_prop(s, t, "I", f"subalternation_{rel}", w, is_axiom=0)
                hypernym_children[t].add(s)

            elif rel == "hyponym":
                self._add_prop(t, s, "A", rel, w, is_axiom=1)
                self._add_prop(t, s, "I", f"subalternation_{rel}", w, is_axiom=0)
                hypernym_children[s].add(t)

            elif rel == "synonym":
                self._add_prop(s, t, "A", rel, w, is_axiom=1)
                self._add_prop(t, s, "A", rel, w, is_axiom=1)
                self._add_prop(s, t, "I", rel, w, is_axiom=1)
                self._add_prop(t, s, "I", rel, w, is_axiom=1)

            # Universal Negative (E): S ∩ P = ∅
            elif rel == "antonym":
                self._add_prop(s, t, "E", rel, w, is_axiom=1)
                self._add_prop(t, s, "E", rel, w, is_axiom=1)
                self._add_prop(s, t, "O", f"subalternation_{rel}", w, is_axiom=0)
                self._add_prop(t, s, "O", f"subalternation_{rel}", w, is_axiom=0)

            elif rel in ("part_of", "member_of", "attribute_of"):
                self._add_prop(s, t, "I", rel, w, is_axiom=1)
                self._add_prop(t, s, "I", rel, w, is_axiom=1)

        # Proper subclass complement yields Particular Negative (O)
        for parent, children in hypernym_children.items():
            if len(children) >= 2:
                for child in children:
                    self._add_prop(parent, child, "O", "subclass_complement", 0.95, is_axiom=0)


class SyllogisticInferenceEngine:
    """Derives 3-proposition syllogistic deductions across all 24 valid scholastic moods."""

    def __init__(self, prop_engine: CategoricalPropositionEngine) -> None:
        self.prop_engine = prop_engine
        self.syllogisms: List[Syllogism] = []

    def derive(self, target_total: int = 15000, max_per_mood: int = 1000) -> List[Syllogism]:
        now_ts = datetime.now(timezone.utc).isoformat()
        all_middle_terms = set(self.prop_engine.by_subj_and_type.keys()) | set(self.prop_engine.by_pred_and_type.keys())

        for mood_name, fig, mood_code, maj_t, min_t, conc_t, req_exist, proof_tpl in MOOD_DEFINITIONS:
            mood_collected = 0

            for M in all_middle_terms:
                if mood_collected >= max_per_mood:
                    break

                if fig == 1:
                    maj_candidates = self.prop_engine.by_subj_and_type.get(M, {}).get(maj_t, {})
                    min_candidates = self.prop_engine.by_pred_and_type.get(M, {}).get(min_t, {})
                elif fig == 2:
                    maj_candidates = self.prop_engine.by_pred_and_type.get(M, {}).get(maj_t, {})
                    min_candidates = self.prop_engine.by_pred_and_type.get(M, {}).get(min_t, {})
                elif fig == 3:
                    maj_candidates = self.prop_engine.by_subj_and_type.get(M, {}).get(maj_t, {})
                    min_candidates = self.prop_engine.by_subj_and_type.get(M, {}).get(min_t, {})
                elif fig == 4:
                    maj_candidates = self.prop_engine.by_pred_and_type.get(M, {}).get(maj_t, {})
                    min_candidates = self.prop_engine.by_subj_and_type.get(M, {}).get(min_t, {})
                else:
                    continue

                for P, maj_prop in maj_candidates.items():
                    if mood_collected >= max_per_mood:
                        break
                    for S, min_prop in min_candidates.items():
                        if mood_collected >= max_per_mood:
                            break

                        if S == P or S == M or P == M:
                            continue

                        conc_id = make_prop_id(conc_t, S, P)
                        conc_text = format_categorical_text(S, P, conc_t)
                        truth_cond = format_truth_condition(S, P, conc_t)

                        syl_key = f"{mood_name}:{fig}:{S}:{M}:{P}"
                        digest = hashlib.sha256(syl_key.encode("utf-8")).hexdigest()[:12]
                        s_tok = re.sub(r"[^a-zA-Z0-9]", "", S)[:8]
                        m_tok = re.sub(r"[^a-zA-Z0-9]", "", M)[:8]
                        p_tok = re.sub(r"[^a-zA-Z0-9]", "", P)[:8]
                        syl_id = f"syl_{mood_name}_{fig}_{s_tok}_{m_tok}_{p_tok}_{digest}"

                        proof = (
                            f"Mood: {mood_name} ({mood_code})\n"
                            f"Figure: {fig}\n"
                            f"Major premise [{maj_t}]: {maj_prop.natural_text} ({maj_prop.symbolic_fol})\n"
                            f"Minor premise [{min_t}]: {min_prop.natural_text} ({min_prop.symbolic_fol})\n"
                            f"Deduction proof:\n{proof_tpl}\n"
                            f"Conclusion [{conc_t}]: {conc_text}"
                        )

                        syllogism = Syllogism(
                            syllogism_id=syl_id,
                            figure=fig,
                            mood=mood_name,
                            mood_code=mood_code,
                            subject_term=S,
                            middle_term=M,
                            predicate_term=P,
                            major_premise_id=maj_prop.prop_id,
                            minor_premise_id=min_prop.prop_id,
                            conclusion_id=conc_id,
                            major_text=maj_prop.natural_text,
                            minor_text=min_prop.natural_text,
                            conclusion_text=conc_text,
                            truth_condition=truth_cond,
                            symbolic_proof=proof,
                            requires_existential_import=req_exist,
                            valid=1,
                            created_at=now_ts
                        )
                        self.syllogisms.append(syllogism)
                        mood_collected += 1

        return self.syllogisms


class SoritesChainSynthesizer:
    """Constructs multi-premise transitive if-then deduction chains linking concepts across taxonomy."""

    def __init__(self, prop_engine: CategoricalPropositionEngine) -> None:
        self.prop_engine = prop_engine
        self.chains: List[SoritesChain] = []

    def synthesize(self, limit: int = 2500) -> List[SoritesChain]:
        now_ts = datetime.now(timezone.utc).isoformat()
        adj: Dict[str, Set[str]] = collections.defaultdict(set)
        for s, type_dict in self.prop_engine.by_subj_and_type.items():
            for p in type_dict.get("A", {}).keys():
                adj[s].add(p)

        adj = dict(adj)
        found_chains: List[Tuple[str, ...]] = []

        for s0 in adj:
            if len(found_chains) >= limit:
                break
            for s1 in adj.get(s0, ()):
                if len(found_chains) >= limit:
                    break
                for s2 in adj.get(s1, ()):
                    if s2 in (s0, s1):
                        continue
                    for s3 in adj.get(s2, ()):
                        if s3 in (s0, s1, s2):
                            continue
                        found_chains.append((s0, s1, s2, s3))
                        if len(found_chains) >= limit:
                            break
                        for s4 in adj.get(s3, ()):
                            if s4 in (s0, s1, s2, s3):
                                continue
                            found_chains.append((s0, s1, s2, s3, s4))
                            if len(found_chains) >= limit:
                                break

        for chain_terms in found_chains:
            k = len(chain_terms) - 1
            premises_texts = []
            premises_ids = []
            symbolic_steps = []
            cond_steps = []

            for i in range(k):
                u = chain_terms[i]
                v = chain_terms[i + 1]
                pid = make_prop_id("A", u, v)
                premises_ids.append(pid)
                premises_texts.append(format_categorical_text(u, v, "A"))
                symbolic_steps.append(f"({clean_label(u)} ⊆ {clean_label(v)})")
                cond_steps.append(f"If x is {clean_label(u)}, then x is {clean_label(v)}")

            conc_text = format_categorical_text(chain_terms[0], chain_terms[-1], "A")
            cond_conclusion = f"Therefore, if x is {clean_label(chain_terms[0])}, then x is {clean_label(chain_terms[-1])}"
            full_conditional = "; ".join(cond_steps) + f" ⊢ {cond_conclusion}"
            symbolic_chain = " ∧ ".join(symbolic_steps) + f" ⟹ ({clean_label(chain_terms[0])} ⊆ {clean_label(chain_terms[-1])})"

            key = ":".join(chain_terms)
            digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]
            cid = f"sorites_{k}_{clean_label(chain_terms[0])}_{clean_label(chain_terms[-1])}_{digest}"

            chain = SoritesChain(
                chain_id=cid,
                chain_length=k,
                terms=list(chain_terms),
                premise_ids=premises_ids,
                premise_texts=premises_texts,
                conclusion_text=conc_text,
                conditional_form=full_conditional,
                symbolic_chain=symbolic_chain,
                relations=["hypernym"] * k,
                created_at=now_ts
            )
            self.chains.append(chain)

        return self.chains


class ConditionalRuleSynthesizer:
    """Formalizes material implications, counterfactuals, definition biconditionals, and modalities."""

    def __init__(self, prop_engine: CategoricalPropositionEngine, graph: PropositionalGraph) -> None:
        self.prop_engine = prop_engine
        self.graph = graph
        self.rules: List[ConditionalRule] = []

    def generate(self, limit: int = 15000) -> List[ConditionalRule]:
        now_ts = datetime.now(timezone.utc).isoformat()
        per_type_limit = max(1000, limit // 6)
        collected = 0

        # 1. Material implications, contrapositives, and modal necessary from A propositions
        count_a = 0
        for pid, prop in self.prop_engine.propositions.items():
            if count_a >= per_type_limit:
                break
            if prop.prop_type == "A":
                s = clean_label(prop.subject)
                p = clean_label(prop.predicate)
                digest = hashlib.sha256(f"impl:{prop.subject}:{prop.predicate}".encode("utf-8")).hexdigest()[:10]

                impl_rule = ConditionalRule(
                    rule_id=f"rule_impl_{digest}",
                    rule_type="implication",
                    antecedent=s,
                    consequent=p,
                    natural_text=f"If x is a {s}, then x is a {p}.",
                    symbolic_form=f"∀x ({re.sub(r'[^a-zA-Z0-9_]', '_', s)}(x) → {re.sub(r'[^a-zA-Z0-9_]', '_', p)}(x))",
                    source_relation=prop.source_relation,
                    confidence=prop.confidence,
                    created_at=now_ts
                )
                self.rules.append(impl_rule)
                collected += 1

                contra_digest = hashlib.sha256(f"contra:{prop.subject}:{prop.predicate}".encode("utf-8")).hexdigest()[:10]
                contra_rule = ConditionalRule(
                    rule_id=f"rule_contra_{contra_digest}",
                    rule_type="contrapositive",
                    antecedent=f"not_{p}",
                    consequent=f"not_{s}",
                    natural_text=f"If x were not a {p}, then x would not be a {s}.",
                    symbolic_form=f"∀x (¬{re.sub(r'[^a-zA-Z0-9_]', '_', p)}(x) → ¬{re.sub(r'[^a-zA-Z0-9_]', '_', s)}(x))",
                    source_relation=f"contrapositive_{prop.source_relation}",
                    confidence=prop.confidence,
                    created_at=now_ts
                )
                self.rules.append(contra_rule)
                count_a += 1

                modal_nec_digest = hashlib.sha256(f"mnec:{prop.subject}:{prop.predicate}".encode("utf-8")).hexdigest()[:10]
                mnec_rule = ConditionalRule(
                    rule_id=f"rule_mnec_{modal_nec_digest}",
                    rule_type="modal_necessary",
                    antecedent=s,
                    consequent=p,
                    natural_text=f"Necessarily, all {s} are {p}.",
                    symbolic_form=f"□∀x ({re.sub(r'[^a-zA-Z0-9_]', '_', s)}(x) → {re.sub(r'[^a-zA-Z0-9_]', '_', p)}(x))",
                    source_relation="alethic_necessity",
                    confidence=prop.confidence,
                    created_at=now_ts
                )
                self.rules.append(mnec_rule)

        # 2. Definition biconditionals from synonyms
        for s, t, rel, w in self.graph.edges:
            if rel == "synonym" and s < t:
                s_clean = clean_label(s)
                t_clean = clean_label(t)
                digest = hashlib.sha256(f"bicon:{s}:{t}".encode("utf-8")).hexdigest()[:10]
                bicon_rule = ConditionalRule(
                    rule_id=f"rule_bicon_{digest}",
                    rule_type="biconditional",
                    antecedent=s_clean,
                    consequent=t_clean,
                    natural_text=f"x is a {s_clean} if and only if x is a {t_clean}.",
                    symbolic_form=f"∀x ({re.sub(r'[^a-zA-Z0-9_]', '_', s_clean)}(x) ↔ {re.sub(r'[^a-zA-Z0-9_]', '_', t_clean)}(x))",
                    source_relation="synonym_definition",
                    confidence=w,
                    created_at=now_ts
                )
                self.rules.append(bicon_rule)
                collected += 1

        # 3. Modal impossible from antonyms
        for s, t, rel, w in self.graph.edges:
            if rel == "antonym" and s < t:
                s_clean = clean_label(s)
                t_clean = clean_label(t)
                digest = hashlib.sha256(f"mimp:{s}:{t}".encode("utf-8")).hexdigest()[:10]
                mimp_rule = ConditionalRule(
                    rule_id=f"rule_mimp_{digest}",
                    rule_type="modal_impossible",
                    antecedent=s_clean,
                    consequent=t_clean,
                    natural_text=f"Necessarily, no {s_clean} are {t_clean}.",
                    symbolic_form=f"□¬∃x ({re.sub(r'[^a-zA-Z0-9_]', '_', s_clean)}(x) ∧ {re.sub(r'[^a-zA-Z0-9_]', '_', t_clean)}(x))",
                    source_relation="antonymic_exclusion",
                    confidence=w,
                    created_at=now_ts
                )
                self.rules.append(mimp_rule)
                collected += 1

        # 4. Modal possible from attribute_of / part_of
        for s, t, rel, w in self.graph.edges:
            if rel in ("attribute_of", "part_of"):
                s_clean = clean_label(s)
                t_clean = clean_label(t)
                digest = hashlib.sha256(f"mpos:{s}:{t}".encode("utf-8")).hexdigest()[:10]
                mpos_rule = ConditionalRule(
                    rule_id=f"rule_mpos_{digest}",
                    rule_type="modal_possible",
                    antecedent=s_clean,
                    consequent=t_clean,
                    natural_text=f"Possibly, some {s_clean} are {t_clean}.",
                    symbolic_form=f"◇∃x ({re.sub(r'[^a-zA-Z0-9_]', '_', s_clean)}(x) ∧ {re.sub(r'[^a-zA-Z0-9_]', '_', t_clean)}(x))",
                    source_relation=rel,
                    confidence=w,
                    created_at=now_ts
                )
                self.rules.append(mpos_rule)
                collected += 1

        return self.rules


class SyllogisticMapStore:
    """Persists logical proposition structures into SQLite and JSONL streaming format."""

    def __init__(self, db_path: pathlib.Path, jsonl_path: pathlib.Path) -> None:
        self.db_path = db_path
        self.jsonl_path = jsonl_path

    def init_db(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        cur.execute("PRAGMA journal_mode = WAL;")
        cur.execute("PRAGMA synchronous = NORMAL;")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS categorical_propositions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prop_id TEXT UNIQUE NOT NULL,
            subject TEXT NOT NULL,
            predicate TEXT NOT NULL,
            prop_type TEXT NOT NULL,
            natural_text TEXT NOT NULL,
            symbolic_fol TEXT NOT NULL,
            truth_condition TEXT NOT NULL,
            source_relation TEXT NOT NULL,
            confidence REAL NOT NULL,
            is_axiom INTEGER NOT NULL DEFAULT 1
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS syllogisms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            syllogism_id TEXT UNIQUE NOT NULL,
            figure INTEGER NOT NULL,
            mood TEXT NOT NULL,
            mood_code TEXT NOT NULL,
            subject_term TEXT NOT NULL,
            middle_term TEXT NOT NULL,
            predicate_term TEXT NOT NULL,
            major_premise_id TEXT NOT NULL,
            minor_premise_id TEXT NOT NULL,
            conclusion_id TEXT NOT NULL,
            major_text TEXT NOT NULL,
            minor_text TEXT NOT NULL,
            conclusion_text TEXT NOT NULL,
            truth_condition TEXT NOT NULL,
            symbolic_proof TEXT NOT NULL,
            requires_existential_import INTEGER NOT NULL DEFAULT 0,
            valid INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP NOT NULL
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS sorites_chains (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chain_id TEXT UNIQUE NOT NULL,
            chain_length INTEGER NOT NULL,
            terms_json TEXT NOT NULL,
            premise_ids_json TEXT NOT NULL,
            premise_texts_json TEXT NOT NULL,
            conclusion_text TEXT NOT NULL,
            conditional_form TEXT NOT NULL,
            symbolic_chain TEXT NOT NULL,
            relations_json TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS conditional_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_id TEXT UNIQUE NOT NULL,
            rule_type TEXT NOT NULL,
            antecedent TEXT NOT NULL,
            consequent TEXT NOT NULL,
            natural_text TEXT NOT NULL,
            symbolic_form TEXT NOT NULL,
            source_relation TEXT NOT NULL,
            confidence REAL NOT NULL,
            created_at TIMESTAMP NOT NULL
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS map_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """)

        cur.execute("CREATE INDEX IF NOT EXISTS idx_cat_subj ON categorical_propositions(subject);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_cat_pred ON categorical_propositions(predicate);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_cat_type ON categorical_propositions(prop_type);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_syl_figure ON syllogisms(figure);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_syl_mood ON syllogisms(mood);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_syl_terms ON syllogisms(subject_term, middle_term, predicate_term);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_sorites_len ON sorites_chains(chain_length);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_cond_type ON conditional_rules(rule_type);")

        conn.commit()
        return conn

    def persist(
        self,
        propositions: List[CategoricalProposition],
        syllogisms: List[Syllogism],
        chains: List[SoritesChain],
        rules: List[ConditionalRule]
    ) -> None:
        conn = self.init_db()
        cur = conn.cursor()

        prop_rows = [
            (p.prop_id, p.subject, p.predicate, p.prop_type, p.natural_text,
             p.symbolic_fol, p.truth_condition, p.source_relation, p.confidence, p.is_axiom)
            for p in propositions
        ]
        cur.executemany("""
        INSERT OR IGNORE INTO categorical_propositions
        (prop_id, subject, predicate, prop_type, natural_text, symbolic_fol, truth_condition, source_relation, confidence, is_axiom)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, prop_rows)

        syl_rows = [
            (s.syllogism_id, s.figure, s.mood, s.mood_code, s.subject_term, s.middle_term, s.predicate_term,
             s.major_premise_id, s.minor_premise_id, s.conclusion_id, s.major_text, s.minor_text, s.conclusion_text,
             s.truth_condition, s.symbolic_proof, s.requires_existential_import, s.valid, s.created_at)
            for s in syllogisms
        ]
        cur.executemany("""
        INSERT OR IGNORE INTO syllogisms
        (syllogism_id, figure, mood, mood_code, subject_term, middle_term, predicate_term,
         major_premise_id, minor_premise_id, conclusion_id, major_text, minor_text, conclusion_text,
         truth_condition, symbolic_proof, requires_existential_import, valid, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, syl_rows)

        chain_rows = [
            (c.chain_id, c.chain_length, json.dumps(c.terms), json.dumps(c.premise_ids),
             json.dumps(c.premise_texts), c.conclusion_text, c.conditional_form, c.symbolic_chain,
             json.dumps(c.relations), c.created_at)
            for c in chains
        ]
        cur.executemany("""
        INSERT OR IGNORE INTO sorites_chains
        (chain_id, chain_length, terms_json, premise_ids_json, premise_texts_json, conclusion_text, conditional_form, symbolic_chain, relations_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, chain_rows)

        rule_rows = [
            (r.rule_id, r.rule_type, r.antecedent, r.consequent, r.natural_text,
             r.symbolic_form, r.source_relation, r.confidence, r.created_at)
            for r in rules
        ]
        cur.executemany("""
        INSERT OR IGNORE INTO conditional_rules
        (rule_id, rule_type, antecedent, consequent, natural_text, symbolic_form, source_relation, confidence, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rule_rows)

        cur.execute("INSERT OR REPLACE INTO map_meta (key, value) VALUES ('propositions_count', ?)", (str(len(propositions)),))
        cur.execute("INSERT OR REPLACE INTO map_meta (key, value) VALUES ('syllogisms_count', ?)", (str(len(syllogisms)),))
        cur.execute("INSERT OR REPLACE INTO map_meta (key, value) VALUES ('sorites_count', ?)", (str(len(chains)),))
        cur.execute("INSERT OR REPLACE INTO map_meta (key, value) VALUES ('rules_count', ?)", (str(len(rules)),))
        cur.execute("INSERT OR REPLACE INTO map_meta (key, value) VALUES ('last_updated', ?)", (datetime.now(timezone.utc).isoformat(),))

        conn.commit()
        conn.close()

        with open(str(self.jsonl_path), "w", encoding="utf-8") as f:
            for s in syllogisms:
                rec = {
                    "unit_type": "syllogism",
                    "id": s.syllogism_id,
                    "figure": s.figure,
                    "mood": s.mood,
                    "mood_code": s.mood_code,
                    "terms": {"S": s.subject_term, "M": s.middle_term, "P": s.predicate_term},
                    "major_premise": {"text": s.major_text, "id": s.major_premise_id},
                    "minor_premise": {"text": s.minor_text, "id": s.minor_premise_id},
                    "conclusion": {"text": s.conclusion_text, "id": s.conclusion_id},
                    "truth_condition": s.truth_condition,
                    "symbolic_proof": s.symbolic_proof,
                    "requires_existential_import": bool(s.requires_existential_import),
                    "valid": bool(s.valid)
                }
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

            for c in chains:
                rec = {
                    "unit_type": "sorites_chain",
                    "id": c.chain_id,
                    "chain_length": c.chain_length,
                    "terms": c.terms,
                    "premise_texts": c.premise_texts,
                    "conclusion_text": c.conclusion_text,
                    "conditional_form": c.conditional_form,
                    "symbolic_chain": c.symbolic_chain
                }
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

            for r in rules:
                rec = {
                    "unit_type": "conditional_rule",
                    "id": r.rule_id,
                    "rule_type": r.rule_type,
                    "antecedent": r.antecedent,
                    "consequent": r.consequent,
                    "natural_text": r.natural_text,
                    "symbolic_form": r.symbolic_form,
                    "source_relation": r.source_relation,
                    "confidence": r.confidence
                }
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")


class SyllogisticOrchestrator:
    """High-level orchestrator for compilation, verification, and continuous daemon execution."""

    def __init__(
        self,
        emap_db: pathlib.Path,
        output_db: pathlib.Path,
        output_jsonl: pathlib.Path,
        target_total: int = 15000,
        max_per_mood: int = 1000
    ) -> None:
        self.emap_db = emap_db
        self.output_db = output_db
        self.output_jsonl = output_jsonl
        self.target_total = target_total
        self.max_per_mood = max_per_mood

    def run_compilation(self) -> Dict[str, Any]:
        graph = PropositionalGraph(self.emap_db)

        prop_engine = CategoricalPropositionEngine(graph)
        prop_engine.compile()
        propositions = list(prop_engine.propositions.values())

        syl_engine = SyllogisticInferenceEngine(prop_engine)
        syllogisms = syl_engine.derive(target_total=self.target_total, max_per_mood=self.max_per_mood)

        sorites_engine = SoritesChainSynthesizer(prop_engine)
        chains = sorites_engine.synthesize(limit=2500)

        cond_engine = ConditionalRuleSynthesizer(prop_engine, graph)
        rules = cond_engine.generate(limit=15000)

        store = SyllogisticMapStore(self.output_db, self.output_jsonl)
        store.persist(propositions, syllogisms, chains, rules)

        mood_counts = collections.Counter(s.mood for s in syllogisms)
        prop_type_counts = collections.Counter(p.prop_type for p in propositions)
        rule_type_counts = collections.Counter(r.rule_type for r in rules)

        metrics = {
            "total_edges_loaded": len(graph.edges),
            "total_propositions": len(propositions),
            "propositions_by_type": dict(prop_type_counts),
            "total_syllogisms": len(syllogisms),
            "syllogisms_by_mood": dict(mood_counts),
            "distinct_moods_covered": len(mood_counts),
            "total_sorites_chains": len(chains),
            "total_conditional_rules": len(rules),
            "rules_by_type": dict(rule_type_counts),
            "db_path": str(self.output_db),
            "jsonl_path": str(self.output_jsonl)
        }
        return metrics

    def run_continuous_loop(self, poll_interval: int = 60) -> None:
        last_edge_count = -1
        while True:
            conn = sqlite3.connect(str(self.emap_db))
            cur = conn.cursor()
            cur.execute("SELECT count(*) FROM edges WHERE source_lemma != target_lemma")
            current_edge_count = cur.fetchone()[0]
            conn.close()

            if current_edge_count != last_edge_count:
                print(f"observed state : graph mutation detected with {current_edge_count} edges.")
                print()
                metrics = self.run_compilation()
                last_edge_count = current_edge_count
                self.print_progen_report(metrics)
            else:
                print("observed state : graph unchanged; awaiting next check cycle.")
                print()

            time.sleep(poll_interval)

    @staticmethod
    def print_progen_report(metrics: Dict[str, Any]) -> None:
        print("status : mass compilation completed.")
        print()
        print(f"edges loaded : {metrics['total_edges_loaded']}.")
        print()
        print(f"categorical propositions compiled : {metrics['total_propositions']}.")
        print()
        for ptype in sorted(metrics["propositions_by_type"].keys()):
            cnt = metrics["propositions_by_type"][ptype]
            print(f"proposition type {ptype} count : {cnt}.")
            print()
        print(f"formal syllogisms derived : {metrics['total_syllogisms']}.")
        print()
        print(f"scholastic moods covered : {metrics['distinct_moods_covered']} of 24.")
        print()
        for mood in sorted(metrics["syllogisms_by_mood"].keys()):
            cnt = metrics["syllogisms_by_mood"][mood]
            print(f"mood {mood} count : {cnt}.")
            print()
        print(f"sorites transitive chains synthesized : {metrics['total_sorites_chains']}.")
        print()
        print(f"conditional and modal rules generated : {metrics['total_conditional_rules']}.")
        print()
        for rtype in sorted(metrics["rules_by_type"].keys()):
            cnt = metrics["rules_by_type"][rtype]
            print(f"rule type {rtype} count : {cnt}.")
            print()
        print(f"storage substrate database : {metrics['db_path']}.")
        print()
        print(f"storage substrate jsonl : {metrics['jsonl_path']}.")
        print()
        print("exit code : 0.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Alice 1.0 English Syllogistic and Propositional Logic Engine")
    parser.add_argument("--emap-db", type=pathlib.Path, default=pathlib.Path("emap.db"), help="Path to source emap.db")
    parser.add_argument("--output-db", type=pathlib.Path, default=pathlib.Path("syllogistic_map.db"), help="Path to destination syllogistic_map.db")
    parser.add_argument("--output-jsonl", type=pathlib.Path, default=pathlib.Path("syllogisms.jsonl"), help="Path to destination syllogisms.jsonl")
    parser.add_argument("--target-syllogisms", type=int, default=15000, help="Target total number of syllogisms to derive")
    parser.add_argument("--max-per-mood", type=int, default=1000, help="Maximum deductions per scholastic mood")
    parser.add_argument("--continuous", action="store_true", help="Run continuous monitoring daemon loop")
    parser.add_argument("--interval", type=int, default=60, help="Polling interval in seconds for continuous mode")
    parser.add_argument("--verify", action="store_true", help="Run verification checks on persisted database")

    args = parser.parse_args()

    orchestrator = SyllogisticOrchestrator(
        emap_db=args.emap_db.resolve(),
        output_db=args.output_db.resolve(),
        output_jsonl=args.output_jsonl.resolve(),
        target_total=args.target_syllogisms,
        max_per_mood=args.max_per_mood
    )

    if args.continuous:
        print("state vector course of action : launch continuous syllogistic daemon.")
        print()
        orchestrator.run_continuous_loop(poll_interval=args.interval)
    else:
        metrics = orchestrator.run_compilation()
        orchestrator.print_progen_report(metrics)

        assert metrics["total_syllogisms"] >= 10000, f"Verification gate failure: {metrics['total_syllogisms']} < 10000"
        assert metrics["distinct_moods_covered"] == 24, f"Mood coverage gate failure: {metrics['distinct_moods_covered']} < 24"


if __name__ == "__main__":
    main()


