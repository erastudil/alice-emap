---
title: "Alice task queue"
version: "1.1.0"
status: active
home: emap/QUEUE.md
spec: emap/SPEC.md
roadmap: emap/ROADMAP.md
---

# queue

One row is one admission. Status is `landed`, `open`, or `blocked`. Owner `local` is deterministic code in this repo. Owner `hydra-free` is a Free Forge call under `prompts/hydra/`. Owner `easylm` edits the EasyLM tree, and only when that wave opens.

| id | wave | task | owner | status | exit |
|---|---|---|---|---|---|
| Q0.1 | W0 | Rewrite `SPEC.md` to the measured lattice, cards, and frames | local | landed | version 1.1.0, baseline counts from `emap.db` |
| Q0.2 | W0 | Write `ROADMAP.md` | local | landed | eight waves, each with an exit |
| Q0.3 | W0 | Write this queue | local | landed | every later row has an owner and an exit |
| Q0.4 | W0 | Draft Hydra repair prompts | local | landed | `prompts/hydra/` system, sense, edge, audit, run |
| Q1.1 | W1 | Add `tools/graph_gate.py` | local | open | prints nodes, walkable edges, quarantine, stub T1, dewey `813.54` |
| Q1.2 | W1 | Resolve `target_id` by lemma join | local | open | walkable rows have both ids set |
| Q1.3 | W1 | Create `edges_quarantine` and move self-loops plus dangling targets | local | open | walkable set has zero self-loops and zero dangling targets |
| Q1.4 | W1 | Export CSR from the walkable set only | local | open | `emap_csr.json` edge_count equals the walkable count |
| Q1.5 | W1 | Keep the lattice tests green after the move | local | open | `python -m pytest -v tests/test_alice_decision_model.py` exits 0 |
| Q2.1 | W2 | Select repair candidates: stub T1 or dewey `813.54` or gloss under eight words | local | open | JSONL of candidate rows, one object per line |
| Q2.2 | W2 | Slice candidates into batches of 10 | local | open | batch files under `prompts/hydra/batches/` |
| Q2.3 | W2 | Run sense repair on each batch | hydra-free | open | raw JSON saved beside the batch, paid GLM untouched |
| Q2.4 | W2 | Run the auditor on each repair | hydra-free | open | accept or reject per lemma with a reason code |
| Q2.5 | W2 | Write back accepted gloss, Dewey, T1, and depth | local | open | rejected rows unchanged. Edges from this pass wait for Q2.6 |
| Q2.6 | W2 | Repair edges among lemmas that both have senses | hydra-free | blocked | waits on Q1.3 so new edges cite real ids |
| Q3.1 | W3 | Frame table module | local | open | one function per frame in `SPEC.md` L1 |
| Q3.2 | W3 | Pointer walk with hop list | local | open | receipt metadata includes the hops |
| Q3.3 | W3 | Wire frames in front of RETRIEVE | local | open | old regex tests still pass through the frames |
| Q3.4 | W3 | Tests for each new frame and for abstain | local | open | pytest exits 0 |
| Q4.1 | W4 | Card compiler for `stacks/*/FACTS.md` | local | open | 1572 cards, ids stable across reruns |
| Q4.2 | W4 | Anchor topics onto walkable lemma ids | local | open | every card has at least one anchor or an explicit unanchored flag |
| Q4.3 | W4 | RETRIEVE returns the card comment and door | local | open | golden prompt file, one hit per card |
| Q4.4 | W4 | Outside-domain file abstains | local | open | null provenance on every row |
| Q5.1 | W5 | Import doors from trusted sources and link indexes | local | open | host allow-list generated, not hand-typed per query |
| Q5.2 | W5 | HAND runs after a card miss or a fresh card | local | open | pinned speed-of-light card never opens a socket |
| Q5.3 | W5 | Unlisted host abstains | local | open | test covers a forced foreign domain |
| Q6.1 | W6 | Feature deck for the surfaces named in `SPEC.md` L3 | local | open | one card per surface |
| Q6.2 | W6 | How-to frame returns the feature card | local | open | one prompt per surface |
| Q7.1 | W7 | COMPOSE rule: scalar card plus convert | local | open | speed of light in miles per hour, two receipt steps |
| Q7.2 | W7 | COMPOSE rule: date card plus day offset | local | open | calendar tool digest on the second step |
| Q7.3 | W7 | Teach walk over the textbook span for the shelf | local | open | returned text is a substring of the textbook file |
| Q8.1 | W8 | Bundle walkable CSR and cards for the browser | easylm | open | answers with zero weight bytes downloaded |
| Q8.2 | W8 | Default EasyLM answerer calls Alice first | easylm | open | generation starts only after abstain plus an explicit request |

## fences on hydra rows

pool: `hydra free` only. Alias `glm` and CheaperInference stay closed while `spend_ledger` for provider `cheaperinference` is at or above $5.00.

writeback: a model response is a candidate file. It becomes a database row only in Q2.5, after Q2.4 accepts it.

batch size: 10 lemmas. A failed batch is retried once. A second failure stays `open` and is not marked complete.
