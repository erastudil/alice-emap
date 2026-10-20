import json
import pathlib
import sqlite3

_CARD = """---
base_model: Qwen/Qwen2.5-3B-Instruct
library_name: peft
pipeline_tag: text-generation
tags:
- lora
- peft
- easylm
- emap
- alice
- knowledge-graph
- tool-use
- function-calling
- qwen
license: apache-2.0
---

# Alice EMap Adapter (Qwen2.5-3B-Instruct)

Discrete low-rank LoRA adapter specializing **Qwen2.5-3B-Instruct** for the **Alice 1.0 EMap** constrained arbitration and evidence-bearing knowledge graph ecosystem.

## Overview

The Alice EMap architecture bridges high-dimensional language representations with an immutable, typed evidence graph:
- **Base Model**: Qwen/Qwen2.5-3B-Instruct
- **Adapter Rank**: r = 16, alpha = 32, dropout 0.05
- **Target Projections**: q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj
- **Topology Inclusion**: Bundled with emap_csr.bin ({lemmas} lemmas, {senses} sense nodes, {edges} CSR edges) and emap_csr.json
- **Specification**: Complete mathematical formulation in SPEC.md
- **GitHub Repository**: [erastudil/alice-emap](https://github.com/erastudil/alice-emap)

## Usage in EasyLM WebGPU

In EasyLM (https://github.com/erastudil/easylm), this adapter can be loaded client-side directly into WebGPU shaders via lora_loader.ts:

```typescript
import {{ parseSafeTensorsHeader, applyLoRAWeights }} from './services/lora_loader';

// Download adapter_model.safetensors from Hugging Face
const buffer = await fetch('https://huggingface.co/Bluebarrels/alice-emap-adapter/resolve/main/adapter_model.safetensors').then(r => r.arrayBuffer());
const {{ header, offset }} = parseSafeTensorsHeader(buffer);
```

## Usage in Hydra CLI

Summon models or route tasks through Hydra with Hugging Face integration:

```bash
hydra hf "Analyze the hypernym distance on Alice emap graph"
```

## Verification

Trained with assistant-only loss masking and verified against the Alice 1.0 property-based arbitration test suite.
"""


def measured_topology(emap_dir: pathlib.Path) -> dict:
    """Lemma, sense, and CSR edge counts from the graph files that ship with the card."""
    csr = json.loads((emap_dir / "emap_csr.json").read_text(encoding="utf-8"))
    with sqlite3.connect(emap_dir / "emap.db") as con:
        lemmas = con.execute("SELECT count(*) FROM lemmas").fetchone()[0]
    return {
        "lemmas": int(lemmas),
        "sense_nodes": int(csr["node_count"]),
        "csr_edges": int(csr["edge_count"]),
    }


def model_card(topology: dict) -> str:
    return _CARD.format(
        lemmas=f"{topology['lemmas']:,}",
        senses=f"{topology['sense_nodes']:,}",
        edges=f"{topology['csr_edges']:,}",
    )


def main() -> None:
    import shutil

    import huggingface_hub

    p = pathlib.Path.home() / ".hydra" / ".env"
    token = ""
    for line in open(p, encoding="utf-8"):
        if line.startswith("HF_TOKEN="):
            token = line.strip().split("=", 1)[1].strip("\"'")

    staging_dir = pathlib.Path("C:/Users/jpm05/Documents/hnai/easylm/output/adapters/alice-emap-adapter")
    staging_dir.mkdir(parents=True, exist_ok=True)

    source_adapter_dir = pathlib.Path("C:/Users/jpm05/Documents/hnai/easylm/output/adapters/hands_qwen2.5-3b-instruct")
    source_emap_dir = pathlib.Path("C:/Users/jpm05/Documents/emap")

    for fname in [
        "adapter_config.json",
        "adapter_model.safetensors",
        "added_tokens.json",
        "merges.txt",
        "special_tokens_map.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "vocab.json",
    ]:
        src = source_adapter_dir / fname
        dst = staging_dir / fname
        if src.exists():
            shutil.copy2(src, dst)

    for fname in ["emap_csr.bin", "emap_csr.json", "SPEC.md"]:
        src = source_emap_dir / fname
        dst = staging_dir / fname
        if src.exists():
            shutil.copy2(src, dst)

    readme_content = model_card(measured_topology(source_emap_dir))

    with open(staging_dir / "README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)

    print(f"Staged {len(list(staging_dir.iterdir()))} files in {staging_dir}")

    api = huggingface_hub.HfApi(token=token)
    repo_id = "Bluebarrels/alice-emap-adapter"
    print(f"Uploading folder to {repo_id}...")
    commit_info = api.upload_folder(
        folder_path=str(staging_dir),
        repo_id=repo_id,
        repo_type="model",
        commit_message="feat: upload alice emap adapter weights, csr topology, and model card"
    )
    print("Upload complete! Commit info:", commit_info)


if __name__ == "__main__":
    main()
