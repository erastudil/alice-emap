---
title: "Alice roadmap"
version: "1.1.0"
status: active
home: emap/ROADMAP.md
spec: emap/SPEC.md
measured: "2026-10-06"
---

# roadmap

Alice becomes the default answerer for any question the stacks or the whitelist can answer. She gets there by binding words to those shelves, then fetching the shelf the words name.

Eight waves. A wave starts when the previous wave's exit command passes. Queue rows live in `QUEUE.md`.

## W0 contract

The spec matches the database and the running router. The repair prompts exist. No model call in this wave.

exit: `SPEC.md` version 1.1.0, this file, `QUEUE.md`, and `prompts/hydra/` are in the tree.

## W1 walkable map

Local code only. Resolve `target_id` where the target lemma already has a sense. Move self-loops and dangling edges into `edges_quarantine`. Export a CSR of the walkable edges.

Hydra stays out. Linking a string to a row that already exists is a join.

exit: graph gate in `SPEC.md` section 10 prints zero null ids, zero self-loops, and zero dangling targets on the walkable set. `pytest` still exits 0.

## W2 sense repair

Hydra Free Forge rewrites gloss, Dewey, and T1 on nodes the gate flags. Paid GLM stays off. The spend ledger is already at $5.06 against a $5.00 ceiling.

A second Hydra call audits the first call. Only rows the auditor accepts are written back. Rejected rows stay as they are and return to the queue.

exit: stub T1 count is zero on repaired nodes. Dewey `813.54` survives only where the gloss is American fiction. A 50-row human sample has zero invented lemmas.

## W3 frames

Replace the three retrieve regular expressions with the L1 frame table. Keep COMPUTE first and ABSTAIN last. Record pointer hops on the receipt. Stamp each receipt with an act from `SPEECH_CANON.md`.

exit: existing lattice tests pass, plus one test per new frame, plus the outside-domain abstain test, plus an act name on every receipt.

## W4 stack cards

Compile EasyLM `stacks/*/FACTS.md` into L2 cards. Anchor each card on lemma ids in the walkable map. A prompt that grounds those anchors returns the comment and the door verbatim.

exit: 1572 cards. Golden prompt per card hits that card. A miss abstains.

## W5 whitelist

Replace the three stored strings with doors from `stacks/TRUSTED_SOURCES.md` and the pack link indexes. HAND runs only when the card is missing or marked fresh. Fetch stays inside the host list.

exit: a pinned constant never opens a socket. An unlisted host abstains. A fresh card returns a span and the door URL.

## W6 feature cards

Compile the EasyLM surface deck in `SPEC.md` section 5 L3. How-to prompts return the procedure card.

exit: one card per named surface. A how-to for each surface hits that card.

## W7 chains and teaching

COMPOSE runs the two-slot rules. Teaching mode returns the next written textbook span for the shelf the frame selected.

exit: "speed of light in miles per hour" fetches the pinned constant, then converts the unit, with both steps on the receipt. A teach prompt returns a textbook span and no new sentence.

## W8 EasyLM default

The browser bundle is the walkable CSR plus the card deck. Alice answers before any weight download. Generation runs only after abstain, when the person asks for it.

exit: a stacks question, a feature how-to, a unit conversion, and an outside-domain prompt each take the route `SPEC.md` names, inside the EasyLM app, with no model weight loaded.
