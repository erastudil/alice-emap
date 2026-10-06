# Alice 1.0 EMap

Alice answers from a word map, a stack of vetted sentences, and a short list of tools. A prompt is matched to a frame and to the words it grounds. The answer is a stored sentence, a tool result, or an honest miss.

## What is in the tree

- `alice_decision_engine.py` walks COMPUTE, then RETRIEVE, then HAND, then ABSTAIN.
- `emap.db` holds 44000 lemmas and 24240 sense nodes. The edge table still needs the walkable-graph pass in `ROADMAP.md`.
- `SPEC.md` is the contract. Version 1.1.0 records the measured baseline and the layers still to build.
- `ROADMAP.md` and `QUEUE.md` are the work order.
- `prompts/hydra/` holds the Free Forge prompts that repair glosses, Dewey codes, and kernel forms.
- `SPEECH_CANON.md` is the rule for what Alice may say, cite, or withhold. The chain behind it is `../TRACTATUS_LOGICO_MECHANICUS.md`. The duty behind it is `../CRITIQUE_OF_MECHANICAL_REASON.md`.

## Verify

```bash
python -m pytest -v tests/test_alice_decision_model.py
```
