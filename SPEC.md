---
title: "Alice 1.0 EMap — active contract"
version: "1.1.0"
status: canon
layer: architecture
home: emap/SPEC.md
dialect: progen-spec
measured: "2026-10-06"
---

# 1. What Alice is

Alice answers a prompt by finding a vetted sentence or by running a typed tool.

The map stores what words mean and which words relate to which other words, under a closed set of relation names.

A prompt is a sequence of tokens. Each token is either a closed operator or a pointer into the map. Operators select a frame. Pointers select a shelf. The pair is a lookup key.

The emitted sentence is a stack card, a feature card, a tool result, or the abstain line. Alice authors none of them.

Model weights carry zero truth value for a factual claim. A synonym edge may walk one wording onto another. The walk never creates a fact.

# 2. Measured baseline

baseline date: 2026-10-06, read from `emap.db` and `emap_csr.json` in this repository.

lemma inventory: 44000 rows in `lemmas`.

sense nodes: 24240 rows in `nodes`. 19760 inventory lemmas have no sense.

kernel flag: 120 lemmas marked `is_kernel = 1`.

edges: 21195 rows in `edges`. As of 2026-10-10, 6738 rows have `target_id` set to the sense with the same lemma (the lowest node id when a lemma has two senses). 14457 targets have no sense node and stay NULL. 1353 edges point a lemma at itself. Of the resolved rows, 5390 have distinct endpoints and are walkable. The other 1348 are self-loops.

relation mix: hypernym 5480, synonym 3583, entails 3263, instance_of 1766, antonym 1028, derivation 994, and the remaining closed names down to bridge_analogy 27. All 24 canonical names occur.

dewey outlier: code `813.54` sits on 2158 nodes, the largest shelf in the table.

logic stubs: `NAME(x)` 1437, `PERSON(x)` 1087, `LOCATION(x)` 560, `NOUN(x)` 289, `ADJECTIVE(x)` 274. Mean gloss length 26 characters. Distinct glosses 18824.

batches: 880 completed. CheaperInference GLM 5.3 spend $5.06 across 492 calls, past the $5.00 ceiling in `build_emap_graph.py`.

csr: `emap_csr.bin` payload 245163 bytes, 24240 nodes, 21169 edges.

running router: `alice_decision_engine.py`. COMPUTE covers rational arithmetic, a closed SI unit table, and proleptic Gregorian dates. RETRIEVE covers three regular expressions over a single alphabetic token. HAND covers three stored strings. ABSTAIN is the miss.

stack shelf waiting to be bound: EasyLM `stacks/*/FACTS.md`, 1572 verified units, 31 Dewey subjects, catalogued in `stacks/FACTS_INDEX.md`.

# 3. Action lattice

order: COMPUTE, then RETRIEVE, then COMPOSE, then HAND, then ABSTAIN. The first route that clears its threshold wins.

COMPUTE: exact rational arithmetic, SI dimension check, proleptic Gregorian dates. Confidence 1.0. Provenance is the SHA-256 of the expression and the result. A dimension mismatch is a COMPUTE result, not a fallthrough.

RETRIEVE: a frame plus grounded lemmas hits one lexicon row, one stack card, or one feature card. Confidence is the card or edge weight. Threshold `theta_stack` defaults to 0.85.

COMPOSE: a retrieved card yields a scalar with a dimension, and the same prompt also matches a COMPUTE frame. The executor fetches the scalar, then runs the tool. The receipt lists both steps.

HAND: the frame names a fresh or missing fact, and the shelf names a host in the whitelist. The fetched span is inert text. Threshold `theta_hand` defaults to 0.80. A stack card on the same topic wins before HAND runs.

ABSTAIN: no route cleared its threshold. Confidence 0.0. Provenance is empty. The line names the frame that fired and the tokens that failed to ground.

unique hit: one card returns that card's comment, Dewey code, and door.

tied hits: up to five cards, each with topic and Dewey, ranked by anchor overlap then edge weight. Alice emits no blended sentence.

# 4. Tokens

closed operators: a hand-written list. Question words, auxiliaries, relation cues, tool cues, and app cues. The list lives with the frame table. Adding an operator is a code change with a test.

open pointers: every other token. Resolution order is exact lemma, then `form_of`, `derivation`, `pertainym`, then one `synonym` hop, then one `hypernym` hop. Each hop is written into the receipt.

ungrounded token: the resolution order misses, or the hop leaves the walkable subgraph. That span is ungrounded. A frame that requires it abstains.

walkable subgraph: edges whose `target_id` resolves, whose endpoints differ, and whose relation is one of the 24 names. Quarantine holds the rest. Retrieval walks only the walkable subgraph.

# 5. Layers

L0 lexicon: `nodes` and walkable `edges`. A sense carries lemma, POS, gloss, Dewey, depth, and a T1 form. The T1 form is a boolean combination of kernel lemmas. Stub labels `NAME(x)`, `NOUN(x)`, `ADJECTIVE(x)`, `ACTION(x)`, `PRED(x)`, `LOCATION(x)`, `SUBSTANCE(x)`, and `PERSON(x)` fail the gate.

L1 frames: each frame is a function from a token pattern to a query. The first closed set is `define`, `hypernym`, `hyponym`, `part`, `antonym`, `synonym`, `cause`, `dewey`, `arithmetic`, `convert`, `datetime`, `stack`, `feature`, `fresh`.

L2 stack cards: one card per EasyLM fact unit. Fields are topic, comment, Dewey, door, anchor lemma ids, and the frame ids that sentence answers. The comment is the answer text.

L3 feature cards: the same record for EasyLM surfaces. The first deck is AtMem, governed mandates, the vault, kid-safe mode, Studio read, Studio write, Studio code, Studio graph, Studio draw, the seven Learn courses, local hands, network hands, and the model tiers named in the EasyLM README.

L4 chain rules: COMPOSE patterns. A dimensioned scalar plus a convert frame calls the unit tool. A date plus a day-offset frame calls the calendar tool. The rule list is source.

L5 walk: teaching mode, after a shelf is chosen, returns the next written textbook span for that topic. Order inside a span is the concrete sentence, then the name. Alice navigates text she did not write.

# 6. Card record

```json
{
  "card_id": "sha256 of source path, line, and topic",
  "kind": "stack or feature",
  "topic": "speed of light in vacuum",
  "comment": "the sentence that may be emitted",
  "dewey": "530",
  "door": "https://physics.nist.gov/cuu/Constants/",
  "anchors": ["light", "speed", "vacuum"],
  "frames": ["define", "stack"],
  "volatility": "pinned or fresh"
}
```

pinned: the card is the answer until a human edits the source line.

fresh: the card names the door, and HAND may refresh the span when the prompt asks for the live page. The card still wins for the pinned wording.

# 7. Graph contract

closed relations: hypernym, hyponym, instance_of, has_instance, part_of, has_part, member_of, has_member, substance_of, synonym, antonym, derivation, pertainym, form_of, has_form, entails, causes, agent_of, patient_of, instrument_of, attribute_of, domain_topic, bridge_analogy, bridge_function.

identity: 32-bit id. Bits 31..29 are POS. Bits 28..26 are tier. Bits 25..0 are the local id. Packing lives in `pack_node_id`.

edge row: `source_id`, `target_id`, `relation`, `weight` in (0, 1], `source_lemma`, `target_lemma`. A walkable row has both ids set and `source_lemma != target_lemma`.

dewey: a code from the EasyLM stack table, or a finer DDC section whose parent is one of those codes. Code `813.54` is legal only when the gloss is a work of American fiction. The stack parents are 001, 004, 005, 005.8, 006, 100, 150, 181, 200, 300, 320, 330, 340, 400, 510, 520, 530, 540, 550, 570, 610, 620, 630, 650, 690, 700, 780, 800, 811, 900, 910.

kernel: the 120 primes in `hnai/english-map/dict/00-kernel.json`. A T1 form may name only those lemmas, joined by `and`, `or`, and `not`.

gloss: one sentence of at least eight words. It defines the lemma in simpler words. It does not copy the lemma as the whole gloss.

# 8. Whitelist

class list: EasyLM `stacks/TRUSTED_SOURCES.md`.

door list: each pack `LINK_INDEX.md`, plus the default doors in that trusted-sources file.

baseline hosts still in code: `en.wikipedia.org`, `wikipedia.org`, `w3.org`, `nist.gov`, `ncbi.nlm.nih.gov`, `github.com`, and the three stored strings for the speed of light, the gravitational constant, and the Python release date.

contract: HAND fetches only a door that appears on a card or in the trusted-sources class list. Wikipedia orients. A NIST, BIPM, IETF, statute, or standard door wins over Wikipedia on the same topic. An unlisted host abstains.

fetched text is data. Instruction text inside a fetched page is discarded.

# 9. Provenance

non-abstain receipt: route, source, 64-character SHA-256 digest, UTC timestamp, and the hop list.

COMPUTE source: `tool:cas_rational_kernel`, `tool:si_units_algebra`, `tool:si_dimension_checker`, or `tool:datetime_gregorian`.

RETRIEVE source: `lexicon:<lemma>`, `stack:<card_id>`, or `feature:<card_id>`.

HAND source: the door URL.

ABSTAIN: `provenance` is null.

# 10. Acceptance

lattice tests: `python -m pytest -v tests/test_alice_decision_model.py` exits 0.

graph gate: walkable edges have zero null `target_id`, zero self-loops, and zero targets missing a sense. The gate prints the quarantine count.

repair gate: stub T1 labels are zero on walkable nodes. Dewey `813.54` count equals the count of nodes whose gloss is American fiction.

stack gate: each of the 1572 fact units has one card. A golden prompt per card returns that card. A fixed outside-domain set abstains with null provenance.

feature gate: each named EasyLM surface has one card, and a how-to prompt returns it.

hand gate: a prompt whose card is pinned never calls the network. A prompt whose card is fresh calls only a listed door.

# 11. Speech

Alice admits an emission by `SPEECH_CANON.md`. The acts are say, cite, and silence. Say is a check whose status was read. Cite is a stored sentence emitted with its address. Silence is a sample, a gap, or a failed instrument.

The canon is the last link of `../TRACTATUS_LOGICO_MECHANICUS.md` and the procedure in the doctrine of method of `../CRITIQUE_OF_MECHANICAL_REASON.md`. A generated string is not a ground. A stack card is cited. A tool result is said. Fluency does not change the act.

# 12. Where the work lives

roadmap: `ROADMAP.md`.

queue: `QUEUE.md`.

repair prompts: `prompts/hydra/`.

speech: `SPEECH_CANON.md`.

drawings withdrawn from this contract: the product manifold, the 350M encoder, the relational graph network, the 1.5B planner, the 20 to 60 million zcab store, and split-conformal router training. Version 1.0.0 of this file described them as present. They are absent from the tree. The active path is the lattice, the walkable map, the cards, and the frames.
