---
title: "Hydra repair runs"
home: emap/prompts/hydra/RUN.md
spec: emap/SPEC.md
queue: emap/QUEUE.md
---

# how to run a repair batch

Pool is Free Forge. The CheaperInference ledger is past the $5.00 ceiling, so `glm` stays unused.

Working directory is the alice-emap repo root.

## 1. Build a batch file

Q2.1 writes candidate rows as JSONL. Q2.2 slices them into objects of 10 rows. Save one slice as `prompts/hydra/batches/sense-0001.json`. The file is a JSON array.

The user prompt is `01-sense-repair.md` with `{{ROWS_JSON}}` replaced by that array.

## 2. Call Hydra

PowerShell, from the repo root:

```powershell
$sys = Get-Content -Raw .\prompts\hydra\00-system.md
$user = Get-Content -Raw .\prompts\hydra\batches\sense-0001.prompt.md
hydra free --system $sys --no-stream --max-tokens 4096 -- $user |
  Set-Content -Encoding utf8 .\prompts\hydra\batches\sense-0001.raw.txt
```

`--` keeps the prompt from being read as an alias. `--no-stream` leaves a single buffer to save. `--max-tokens 4096` fits ten repaired rows.

If the raw file is empty or is not a JSON array, run the same command once more. A second failure leaves the batch `open` in `QUEUE.md`.

## 3. Audit

Fill `03-audit.md`. `{{ALLOW_JSON}}` is the kernel lemma list plus the ten batch lemmas. `{{INPUT_JSON}}` is the original slice. `{{PROPOSED_JSON}}` is the parsed array from the raw file.

```powershell
$sys = Get-Content -Raw .\prompts\hydra\00-system.md
$user = Get-Content -Raw .\prompts\hydra\batches\sense-0001.audit.md
hydra free --system $sys --no-stream --max-tokens 2048 -- $user |
  Set-Content -Encoding utf8 .\prompts\hydra\batches\sense-0001.audit.txt
```

## 4. Write back

Q2.5 reads the audit file. `verdict` `accept` updates `gloss`, `dewey`, `t1_decomposition`, and `depth` for that lemma. `reject` leaves the row. Edges proposed in the same response are kept in the batch file and applied in Q2.6, after the walkable-graph pass. The raw model text never goes straight into `emap.db`.

## 5. Edges, after the graph gate

Q2.6 waits until Q1.3 has quarantined dangling edges. Use `02-edge-repair.md` the same way, on rows whose sense repair was accepted. The auditor runs again before writeback.

## What the model is for

The model rewrites a gloss, picks a Dewey parent, writes a kernel form, and names relations to lemmas already on the allow-list.

Joining `target_lemma` to `nodes.id` is a SQL update in Q1.2. That step does not call Hydra.
