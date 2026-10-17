#!/usr/bin/env python3
"""
build_bridge_edges.py — Deterministic Scientific, Philosophical & Stacks Co-occurrence
Bridge-Edge Builder for Alice 1.0 EMap (`emap.db` -> `emap_csr.bin` + `emap_lexicon.jsonl`).

1. Ensures core scientific, logical, and Socratic lemmas exist as grounded sense nodes in `emap.db`.
2. Adds bidirectional curated causal/conceptual bridge chains across Physics, Chemistry, Biology,
   Economics, Logic, Socratic Dialectic, and Computing using canonical EMap relations.
3. Mines deterministic definition/fact bridge edges (`topic <-> key_terms`) from:
   - `easylm/data/facts.db` (32 Stacks `FACTS.md`)
   - `kb/facts.db` (verified sovereign facts)
   - `snowgate-alice/rust-backend/data/textbooks_v0_1698.jsonl` (co-occurring domain concepts)
4. Runs `quarantine_unwalkable_edges` + `resolve_target_ids`, compiles `emap_csr.bin` and
   `emap_lexicon.jsonl`, and copies both to `snowgate-alice/rust-backend/data/unified/`.
"""

from __future__ import annotations

import json
import math
import re
import shutil
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

EMAP_ROOT = Path(r"C:\Users\jpm05\Documents\emap")
if str(EMAP_ROOT) not in sys.path:
    sys.path.insert(0, str(EMAP_ROOT))

from build_emap_graph import (
    CANONICAL_RELATIONS,
    export_csr,
    get_db,
    pack_node_id,
    quarantine_unwalkable_edges,
    resolve_target_ids,
)

EASYLM_FACTS_DB = Path(r"C:\Users\jpm05\Documents\easylm\data\facts.db")
KB_FACTS_DB = Path(r"C:\Users\jpm05\Documents\kb\facts.db")
TEXTBOOKS_JSONL = Path(r"C:\Users\jpm05\Documents\snowgate-alice\rust-backend\data\textbooks_v0_1698.jsonl")
UNIFIED_DIR = Path(r"C:\Users\jpm05\Documents\snowgate-alice\rust-backend\data\unified")

STOPWORDS = {
    "the", "and", "for", "that", "this", "with", "from", "are", "was", "were",
    "have", "has", "had", "not", "but", "what", "all", "can", "when", "where",
    "which", "who", "will", "more", "one", "two", "three", "into", "than",
    "then", "them", "they", "their", "there", "been", "being", "also", "such",
    "only", "other", "some", "over", "under", "between", "through", "during",
    "before", "after", "above", "below", "each", "every", "both", "either",
    "neither", "while", "because", "therefore", "thus", "hence", "about",
    "does", "did", "would", "could", "should", "may", "might", "must", "shall",
    "its", "his", "her", "our", "your", "any", "many", "much", "most", "very",
    "same", "different", "used", "using", "called", "known", "defined", "form",
    "part", "kind", "type", "system", "state", "process", "property", "value",
}

# Core lemmas that must exist in `nodes` as grounded Stage-1 concepts
REQUIRED_CONCEPTS = [
    ("gravity", "N", "530", "ATTRACTION_FORCE(mass_1, mass_2)", 2, "universal attractive interaction between all bodies possessing mass and energy"),
    ("mass", "N", "530", "INERTIA_QUANTITY(matter)", 2, "intrinsic property of a physical body measuring its inertia and gravitational coupling"),
    ("force", "N", "530", "CAUSE_ACCELERATION(mass, acceleration)", 2, "interaction that changes the motion or momentum of a physical body (F = ma)"),
    ("acceleration", "N", "530", "RATE_OF_CHANGE(velocity, time)", 2, "rate of change of velocity of an object with respect to time"),
    ("velocity", "N", "530", "RATE_OF_CHANGE(position, time)", 2, "directional speed of a body in motion"),
    ("momentum", "N", "530", "PRODUCT(mass, velocity)", 2, "conserved vector quantity equal to the product of mass and velocity"),
    ("energy", "N", "530", "CAPACITY_FOR_WORK(system)", 1, "conserved quantitative property transferred to perform work or generate heat"),
    ("work", "N", "530", "INTEGRAL(force, displacement)", 2, "energy transferred to or from an object via the application of force along a displacement"),
    ("power", "N", "530", "RATE_OF_CHANGE(work, time)", 2, "rate of doing work or transferring energy per unit time"),
    ("heat", "N", "530", "THERMAL_ENERGY_TRANSFER(temperature_gradient)", 2, "thermal energy transferred between systems due to a temperature difference"),
    ("entropy", "N", "530", "LOG_MICROSTATES(system)", 2, "thermodynamic quantity measuring the number of microscopic configurations and irreversibility"),
    ("thermodynamics", "N", "530", "SCIENCE_OF(heat, work, entropy)", 2, "branch of physics governing heat, work, temperature, and energy conservation"),
    ("wave", "N", "530", "PROPAGATING_OSCILLATION(field, medium)", 2, "propagating dynamic disturbance that transfers energy through space or a medium"),
    ("frequency", "N", "530", "CYCLES_PER_TIME(wave)", 2, "number of occurrences of a repeating wave event per unit of time"),
    ("wavelength", "N", "530", "SPATIAL_PERIOD(wave)", 2, "spatial distance over which a periodic wave's shape repeats"),
    ("photon", "N", "530", "QUANTUM_PARTICLE(electromagnetic_field)", 3, "elementary quantum of light and all other forms of electromagnetic radiation"),
    ("light", "N", "530", "ELECTROMAGNETIC_RADIATION(photon)", 2, "electromagnetic radiation that propagates as transverse waves and photon quanta"),
    ("atom", "N", "540", "BOUND_SYSTEM(nucleus, electron)", 2, "smallest unit of ordinary matter that forms a chemical element"),
    ("nucleus", "N", "530", "CORE_BOUND(proton, neutron)", 3, "dense positively charged core of an atom composed of protons and neutrons"),
    ("proton", "N", "530", "BARYON_POSITIVE(nucleus)", 3, "stable subatomic hadron in the atomic nucleus carrying positive elementary charge +1e"),
    ("neutron", "N", "530", "BARYON_NEUTRAL(nucleus)", 3, "subatomic hadron in the atomic nucleus with zero net electric charge"),
    ("electron", "N", "530", "LEPTON_NEGATIVE(atom, charge)", 3, "elementary subatomic lepton carrying negative electric charge -1e"),
    ("charge", "N", "530", "ELECTROMAGNETIC_COUPLING(matter)", 2, "conserved physical property of matter that causes it to experience a force in an electromagnetic field"),
    ("current", "N", "530", "FLOW_RATE(charge, time)", 2, "net flow of electric charge per unit time through a conducting medium"),
    ("voltage", "N", "530", "POTENTIAL_DIFFERENCE(energy, charge)", 2, "electric potential difference per unit charge between two points in an electric field"),
    ("resistance", "N", "530", "OPPOSITION_TO_FLOW(voltage, current)", 2, "measure of opposition to electric current flow (R = V / I)"),
    ("molecule", "N", "540", "COVALENT_GROUP(atom)", 2, "electrically neutral group of two or more atoms held together by chemical bonds"),
    ("element", "N", "540", "PURE_SUBSTANCE(atomic_number)", 2, "chemical species whose atoms all have the same number of protons in their nuclei"),
    ("reaction", "N", "540", "TRANSFORMATION(reactant, product)", 2, "process that leads to the chemical transformation of one set of chemical substances to another"),
    ("dna", "N", "570", "NUCLEIC_ACID_POLYMER(gene, nucleotide)", 3, "deoxyribonucleic acid macromolecule carrying hereditary genetic instructions"),
    ("rna", "N", "570", "RIBONUCLEIC_POLYMER(transcription, translation)", 3, "ribonucleic acid polymeric molecule essential for coding, decoding, and expression of genes"),
    ("gene", "N", "570", "HEREDITARY_UNIT(dna, protein)", 2, "distinct sequence of nucleotides in DNA or RNA that encodes a functional protein or RNA molecule"),
    ("chromosome", "N", "570", "PACKAGED_STRUCTURE(dna, gene)", 3, "long DNA molecule containing part or all of the genetic material of an organism"),
    ("protein", "N", "570", "POLYPEPTIDE_CHAIN(amino_acid)", 2, "large biomolecule folded from chains of amino acid residues encoded by genes"),
    ("enzyme", "N", "570", "BIOLOGICAL_CATALYST(protein, reaction)", 3, "protein macromolecule that acts as a biological catalyst to accelerate chemical reactions"),
    ("cell", "N", "570", "FUNDAMENTAL_UNIT(life, organism)", 2, "basic membrane-bound structural and functional unit of all known living organisms"),
    ("organism", "N", "570", "LIVING_SYSTEM(cell, metabolism)", 2, "contiguous living system capable of metabolism, homeostasis, growth, and reproduction"),
    ("evolution", "N", "570", "DESCENT_WITH_MODIFICATION(gene, selection)", 2, "change in the heritable characteristics of biological populations over successive generations"),
    ("photosynthesis", "N", "570", "PHOTOCHEMICAL_SYNTHESIS(light, glucose)", 3, "biological process by which green plants convert light energy into chemical energy in carbohydrates"),
    ("chlorophyll", "N", "570", "PHOTORECEPTOR_PIGMENT(photosynthesis)", 3, "green magnesium-porphyrin pigment in chloroplasts that absorbs light for photosynthesis"),
    ("supply", "N", "330", "QUANTITY_OFFERED(market, price)", 2, "total amount of a specific good or service available to consumers at a given price schedule"),
    ("demand", "N", "330", "QUANTITY_DESIRED(market, price)", 2, "consumer willingness and ability to purchase a quantity of goods or services at a given price"),
    ("price", "N", "330", "EXCHANGE_RATIO(supply, demand)", 2, "monetary quantity of payment or compensation given by one party to another in return for goods"),
    ("market", "N", "330", "EXCHANGE_SYSTEM(buyer, seller)", 2, "institutional mechanism where buyers and sellers exchange goods, services, and information"),
    ("inflation", "N", "330", "PRICE_LEVEL_INCREASE(currency, time)", 2, "sustained increase in the general price level of goods and services and fall in purchasing power"),
    ("premise", "N", "160", "PROPOSITION_ASSUMED(inference, conclusion)", 2, "proposition supporting or helping to justify a conclusion in a logical argument"),
    ("conclusion", "N", "160", "PROPOSITION_DERIVED(premise, inference)", 2, "proposition reached by valid deductive or inductive inference from given premises"),
    ("validity", "N", "160", "TRUTH_PRESERVING_FORM(premise, conclusion)", 2, "logical property of an argument whereby if all premises are true, the conclusion cannot be false"),
    ("truth", "N", "160", "CORRESPONDENCE_REALITY(proposition, fact)", 1, "property of propositions that accord with empirical fact and logical necessity"),
    ("proof", "N", "510", "DEDUCTIVE_DERIVATION(axiom, theorem)", 2, "inferential argument for a mathematical or logical statement showing that assumptions guarantee the conclusion"),
    ("axiom", "N", "510", "FOUNDATIONAL_PROPOSITION(proof, system)", 2, "unproven foundational proposition taken as a starting point for deducing theorems"),
    ("theorem", "N", "510", "PROVEN_PROPOSITION(axiom, proof)", 2, "statement that has been proved on the basis of explicitly stated axioms and deductive rules"),
    ("thesis", "N", "160", "INITIAL_PROPOSITION(dialectic)", 2, "intellectual proposition or definitional claim advanced for dialectical cross-examination"),
    ("antithesis", "N", "160", "COUNTER_PROPOSITION(thesis, dialectic)", 2, "direct contrast, counterexample, or opposing proposition pitted against a thesis in dialectic"),
    ("synthesis", "N", "160", "SUBLATED_INTEGRATION(thesis, antithesis)", 2, "higher-order resolution that preserves true commitments of thesis and antithesis while removing contradiction"),
    ("dialectic", "N", "160", "METHOD_OF_INQUIRY(thesis, antithesis, synthesis)", 2, "structured discourse between opposing perspectives to establish truth through reasoned examination"),
    ("contradiction", "N", "160", "CONJUNCTION_INCOMPATIBLE(proposition, negation)", 2, "logical incompatibility between two or more propositions that cannot simultaneously be true"),
    ("question", "N", "160", "INTERROGATIVE_PROBE(inquiry, answer)", 1, "linguistic expression used to make a request for information or test a boundary commitment"),
    ("aporia", "N", "160", "HONEST_IMPASSE(elenchus, wonder)", 3, "Socratic state of honest puzzlement and recognition of ignorance when unexamined dogma collapses"),
    ("elenchus", "N", "160", "CROSS_EXAMINATION_REFUTATION(thesis, counterexample)", 3, "Socratic method of cross-examining a definition against boundary counterexamples to expose latent contradiction"),
    ("maieutics", "N", "160", "SOCRATIC_MIDWIFERY(aporia, synthesis)", 3, "Socratic art of intellectual midwifery that helps an interlocutor give birth to a refined, bounded definition"),
    ("counterexample", "N", "160", "FALSIFYING_INSTANCE(universal_claim)", 2, "specific boundary case that refutes a universal proposition of the form ForAll(x, P(x))"),
    ("falsifiability", "N", "001", "CAPACITY_FOR_REFUTATION(hypothesis, observation)", 2, "Popperian demarcation criterion requiring that a scientific claim admit observable counter-instances"),
    ("socrates", "N", "180", "PHILOSOPHER_OF(elenchus, aporia)", 2, "classical Athenian philosopher who founded Western ethical inquiry and the elenctic method"),
]

# Explicit curated bidirectional bridge pairs: (lemma_a, lemma_b, forward_rel, reverse_rel, weight)
CURATED_BRIDGES = [
    # Physics: Mechanics, Gravitation, Energy, Waves
    ("gravity", "mass", "attribute_of", "causes", 0.98),
    ("gravity", "force", "hypernym", "hyponym", 0.97),
    ("gravity", "acceleration", "causes", "attribute_of", 0.96),
    ("gravity", "orbit", "causes", "entails", 0.94),
    ("gravity", "weight", "causes", "attribute_of", 0.95),
    ("mass", "force", "entails", "attribute_of", 0.97),
    ("mass", "acceleration", "bridge_function", "bridge_function", 0.95),
    ("mass", "momentum", "part_of", "has_part", 0.96),
    ("mass", "energy", "bridge_function", "bridge_function", 0.97),
    ("mass", "weight", "causes", "attribute_of", 0.95),
    ("force", "acceleration", "causes", "attribute_of", 0.98),
    ("force", "work", "causes", "entails", 0.96),
    ("force", "momentum", "causes", "attribute_of", 0.95),
    ("force", "pressure", "causes", "attribute_of", 0.93),
    ("acceleration", "velocity", "attribute_of", "has_attribute" if "has_attribute" in CANONICAL_RELATIONS else "entails", 0.96),
    ("velocity", "momentum", "part_of", "has_part", 0.96),
    ("velocity", "speed", "synonym", "synonym", 0.92),
    ("energy", "work", "entails", "causes", 0.98),
    ("energy", "power", "attribute_of", "entails", 0.95),
    ("energy", "heat", "has_instance", "instance_of", 0.95),
    ("energy", "thermodynamics", "domain_topic", "has_part", 0.94),
    ("heat", "temperature", "causes", "attribute_of", 0.96),
    ("heat", "entropy", "causes", "attribute_of", 0.95),
    ("entropy", "thermodynamics", "domain_topic", "has_part", 0.96),
    ("wave", "frequency", "has_part", "attribute_of", 0.96),
    ("wave", "wavelength", "has_part", "attribute_of", 0.96),
    ("frequency", "wavelength", "bridge_function", "bridge_function", 0.96),
    ("light", "photon", "substance_of", "part_of", 0.97),
    ("light", "wave", "hypernym", "hyponym", 0.95),
    ("photon", "energy", "attribute_of", "has_instance", 0.94),

    # Chemistry & Electromagnetism
    ("atom", "nucleus", "has_part", "part_of", 0.98),
    ("atom", "electron", "has_part", "part_of", 0.98),
    ("atom", "proton", "has_part", "part_of", 0.98),
    ("atom", "neutron", "has_part", "part_of", 0.97),
    ("atom", "element", "part_of", "substance_of", 0.96),
    ("atom", "molecule", "part_of", "has_part", 0.97),
    ("nucleus", "proton", "has_part", "part_of", 0.98),
    ("nucleus", "neutron", "has_part", "part_of", 0.98),
    ("electron", "charge", "attribute_of", "attribute_of", 0.97),
    ("proton", "charge", "attribute_of", "attribute_of", 0.97),
    ("charge", "current", "causes", "entails", 0.97),
    ("current", "voltage", "bridge_function", "causes", 0.96),
    ("voltage", "resistance", "bridge_function", "bridge_function", 0.95),
    ("current", "resistance", "bridge_function", "bridge_function", 0.95),
    ("molecule", "reaction", "patient_of", "agent_of", 0.94),
    ("element", "periodic", "domain_topic", "domain_topic", 0.92),

    # Biology & Genetics
    ("dna", "gene", "has_part", "part_of", 0.98),
    ("dna", "chromosome", "part_of", "substance_of", 0.98),
    ("dna", "rna", "causes", "derivation", 0.96),
    ("dna", "cell", "part_of", "has_part", 0.96),
    ("gene", "chromosome", "part_of", "has_part", 0.97),
    ("gene", "protein", "causes", "entails", 0.97),
    ("gene", "evolution", "instrument_of", "entails", 0.95),
    ("rna", "protein", "causes", "entails", 0.96),
    ("protein", "enzyme", "has_instance", "hypernym", 0.96),
    ("protein", "cell", "part_of", "has_part", 0.95),
    ("enzyme", "reaction", "causes", "instrument_of", 0.95),
    ("cell", "organism", "part_of", "has_part", 0.98),
    ("cell", "nucleus", "has_part", "part_of", 0.95),
    ("photosynthesis", "chlorophyll", "instrument_of", "agent_of", 0.97),
    ("photosynthesis", "light", "entails", "causes", 0.95),
    ("photosynthesis", "plant", "attribute_of", "agent_of", 0.95),

    # Economics & Finance
    ("supply", "demand", "antonym", "antonym", 0.97),
    ("supply", "price", "causes", "bridge_function", 0.97),
    ("demand", "price", "causes", "bridge_function", 0.97),
    ("price", "market", "attribute_of", "has_part", 0.97),
    ("supply", "market", "domain_topic", "has_part", 0.96),
    ("demand", "market", "domain_topic", "has_part", 0.96),
    ("market", "trade", "entails", "domain_topic", 0.95),
    ("price", "inflation", "causes", "entails", 0.95),
    ("money", "currency", "synonym", "synonym", 0.96),
    ("money", "inflation", "attribute_of", "attribute_of", 0.94),
    ("capital", "market", "domain_topic", "has_part", 0.94),

    # Logic, Epistemology & Socratic Dialectic
    ("premise", "conclusion", "entails", "derivation", 0.98),
    ("premise", "validity", "part_of", "entails", 0.96),
    ("conclusion", "validity", "part_of", "entails", 0.96),
    ("validity", "truth", "bridge_function", "attribute_of", 0.96),
    ("premise", "truth", "attribute_of", "attribute_of", 0.94),
    ("axiom", "theorem", "entails", "derivation", 0.98),
    ("axiom", "proof", "part_of", "entails", 0.97),
    ("proof", "theorem", "causes", "entails", 0.98),
    ("proof", "truth", "entails", "attribute_of", 0.96),
    ("thesis", "antithesis", "antonym", "antonym", 0.98),
    ("thesis", "synthesis", "part_of", "has_part", 0.97),
    ("antithesis", "synthesis", "causes", "has_part", 0.98),
    ("thesis", "dialectic", "domain_topic", "has_part", 0.96),
    ("antithesis", "dialectic", "domain_topic", "has_part", 0.96),
    ("synthesis", "dialectic", "domain_topic", "has_part", 0.96),
    ("antithesis", "counterexample", "synonym", "synonym", 0.96),
    ("counterexample", "contradiction", "causes", "entails", 0.96),
    ("counterexample", "falsifiability", "instrument_of", "entails", 0.96),
    ("question", "aporia", "causes", "entails", 0.97),
    ("question", "elenchus", "part_of", "has_part", 0.97),
    ("elenchus", "aporia", "causes", "entails", 0.98),
    ("elenchus", "counterexample", "instrument_of", "part_of", 0.97),
    ("elenchus", "contradiction", "causes", "entails", 0.96),
    ("aporia", "maieutics", "causes", "entails", 0.97),
    ("maieutics", "synthesis", "causes", "synonym", 0.96),
    ("socrates", "elenchus", "agent_of", "domain_topic", 0.97),
    ("socrates", "aporia", "agent_of", "domain_topic", 0.97),
    ("socrates", "maieutics", "agent_of", "domain_topic", 0.97),
]


def tokenize_words(s: str) -> list[str]:
    return [w for w in re.findall(r"[a-z]{3,}", s.lower()) if w not in STOPWORDS]


def main():
    db = get_db()
    cur = db.cursor()

    # 1. Load existing lemmas and nodes
    cur.execute("SELECT lemma, idx FROM lemmas")
    lemma_to_idx = {r[0]: r[1] for r in cur.fetchall()}
    max_lemma_idx = max(lemma_to_idx.values()) if lemma_to_idx else 50000

    cur.execute("SELECT lemma, id, t1_decomposition FROM nodes ORDER BY id")
    node_map = {}
    for lem, nid, t1 in cur.fetchall():
        if lem not in node_map:
            node_map[lem] = (nid, t1)

    added_nodes = 0
    for lem, pos, dewey, t1, depth, gloss in REQUIRED_CONCEPTS:
        if lem not in lemma_to_idx:
            max_lemma_idx += 1
            lemma_to_idx[lem] = max_lemma_idx
            cur.execute(
                "INSERT OR IGNORE INTO lemmas (idx, lemma, is_kernel, category) VALUES (?, ?, 1, ?)",
                (max_lemma_idx, lem, dewey),
            )
        if lem not in node_map:
            local_id = lemma_to_idx[lem]
            nid = pack_node_id(pos, tier=0, local_id=local_id)
            sense_id = f"{lem}.{pos.lower()}.01"
            lorentz_r = math.log(1.0 + depth)
            cur.execute(
                """
                INSERT OR REPLACE INTO nodes (id, lemma, pos, tier, sense_id, gloss, dewey, t1_decomposition, depth, lorentz_r)
                VALUES (?, ?, ?, 0, ?, ?, ?, ?, ?, ?)
                """,
                (nid, lem, pos, sense_id, gloss, dewey, t1, depth, lorentz_r),
            )
            node_map[lem] = (nid, t1)
            added_nodes += 1
        else:
            # Ensure T1 decomposition is grounded (not a stub label)
            nid, existing_t1 = node_map[lem]
            if existing_t1.strip().upper() in {
                "NAME(X)", "NOUN(X)", "ADJECTIVE(X)", "ACTION(X)",
                "PRED(X)", "LOCATION(X)", "SUBSTANCE(X)", "PERSON(X)", ""
            }:
                cur.execute(
                    "UPDATE nodes SET t1_decomposition = ?, gloss = ? WHERE id = ?",
                    (t1, gloss, nid),
                )
                node_map[lem] = (nid, t1)

    db.commit()
    print(f"[1/4] Verified required concept nodes (+{added_nodes} new nodes added; total sensed lemmas: {len(node_map)})")

    edges_to_insert = []

    def queue_edge(src_lem: str, dst_lem: str, rel: str, weight: float):
        if src_lem == dst_lem:
            return
        if src_lem not in node_map or dst_lem not in node_map:
            return
        if rel not in CANONICAL_RELATIONS:
            rel = "bridge_function"
        src_id = node_map[src_lem][0]
        dst_id = node_map[dst_lem][0]
        edges_to_insert.append((src_id, dst_id, rel, round(float(weight), 4), src_lem, dst_lem))

    # 2. Add curated bidirectional scientific/philosophical bridges
    for a, b, rel_ab, rel_ba, w in CURATED_BRIDGES:
        queue_edge(a, b, rel_ab, w)
        queue_edge(b, a, rel_ba, w)

    # 3. Mine deterministic topic <-> comment bridges from stack_cards.jsonl, easylm/data/facts.db, and kb/facts.db
    mined_fact_pairs = 0
    raw_tc_pairs = []
    stack_cards_path = UNIFIED_DIR / "stack_cards.jsonl"
    if stack_cards_path.exists():
        with open(stack_cards_path, "r", encoding="utf-8") as scf:
            for line in scf:
                if not line.strip():
                    continue
                c_obj = json.loads(line)
                raw_tc_pairs.append((c_obj.get("topic", ""), c_obj.get("comment", "")))

    for fdb_path, sql_q in [
        (EASYLM_FACTS_DB, "SELECT topic, comment FROM units"),
        (KB_FACTS_DB, "SELECT topic, comment FROM facts"),
    ]:
        if not fdb_path.exists():
            continue
        try:
            fconn = sqlite3.connect(str(fdb_path))
            fcur = fconn.cursor()
            fcur.execute(sql_q)
            raw_tc_pairs.extend(fcur.fetchall())
            fconn.close()
        except Exception:
            pass

    for topic_raw, comment_raw in raw_tc_pairs:
        t_words = [w for w in tokenize_words(str(topic_raw or "")) if w in node_map]
        c_words = [w for w in tokenize_words(str(comment_raw or "")) if w in node_map]
        if not t_words or not c_words:
            continue
        for tw in t_words[:2]:
            linked = 0
            for cw in c_words:
                if cw != tw:
                    queue_edge(tw, cw, "domain_topic", 0.88)
                    queue_edge(cw, tw, "domain_topic", 0.88)
                    mined_fact_pairs += 1
                    linked += 1
                    if linked >= 3:
                        break

    # 4. Mine high-confidence co-occurring concept pairs within the same textbook paragraph
    pair_counts = Counter()
    if TEXTBOOKS_JSONL.exists():
        with open(TEXTBOOKS_JSONL, "r", encoding="utf-8") as tf:
            for line in tf:
                if not line.strip():
                    continue
                obj = json.loads(line)
                words = []
                seen = set()
                for w in tokenize_words(obj.get("text", "")):
                    if w in node_map and len(w) >= 4 and w not in seen:
                        seen.add(w)
                        words.append(w)
                    if len(words) >= 12:
                        break
                for i in range(len(words)):
                    for j in range(i + 1, len(words)):
                        a, b = sorted((words[i], words[j]))
                        pair_counts[(a, b)] += 1

    cooccur_added = 0
    for (a, b), cnt in pair_counts.most_common(2500):
        if cnt < 3:
            break
        w = min(0.92, 0.78 + 0.02 * cnt)
        queue_edge(a, b, "bridge_function", w)
        queue_edge(b, a, "bridge_function", w)
        cooccur_added += 1

    cur.executemany(
        """
        INSERT OR REPLACE INTO edges (source_id, target_id, relation, weight, source_lemma, target_lemma)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        edges_to_insert,
    )
    db.commit()
    print(f"[2/4] Queued {len(edges_to_insert)} bridge edge records (fact pairs: {mined_fact_pairs}, textbook co-occur pairs: {cooccur_added})")

    q_stats = quarantine_unwalkable_edges(db)
    resolved = resolve_target_ids(db)
    print(f"[3/4] Quarantine check: {q_stats}, target_ids resolved: {resolved}")

    # Export CSR binary
    csr_bin_path = EMAP_ROOT / "emap_csr.bin"
    csr_json_path = EMAP_ROOT / "emap_csr.json"
    export_csr(db, out_bin=csr_bin_path, out_meta=csr_json_path)

    # Export emap_lexicon.jsonl ordered by `SELECT ... FROM nodes ORDER BY id`
    lex_path = UNIFIED_DIR / "emap_lexicon.jsonl"
    cur.execute(
        "SELECT id, lemma, pos, tier, sense_id, gloss, dewey, t1_decomposition, depth, lorentz_r FROM nodes ORDER BY id"
    )
    rows = cur.fetchall()
    with open(lex_path, "w", encoding="utf-8", newline="\n") as lf:
        for csr_idx, (nid, lem, pos, tier, sid, gloss, dewey, t1, depth, lr) in enumerate(rows):
            rec = {
                "csr_idx": csr_idx,
                "node_id": nid,
                "lemma": lem,
                "pos": pos,
                "tier": tier,
                "sense_id": sid,
                "dewey": dewey,
                "t1_decomposition": t1,
                "depth": depth,
                "lorentz_r": round(float(lr), 6),
                "gloss": gloss,
            }
            lf.write(json.dumps(rec, ensure_ascii=False) + "\n")

    shutil.copy2(csr_bin_path, UNIFIED_DIR / "emap_csr.bin")
    shutil.copy2(csr_json_path, UNIFIED_DIR / "emap_csr.json")
    print(f"[4/4] Synced emap_csr.bin and emap_lexicon.jsonl ({len(rows)} nodes) -> {UNIFIED_DIR}")
    db.close()


if __name__ == "__main__":
    main()
