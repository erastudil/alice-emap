"""tools/run_repair_batch.py - Automated Sense Repair and Audit Harness via Hydra Free."""

import json
import os
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

# Ensure UTF-8 output streams
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "emap.db"
PROMPTS_DIR = ROOT / "prompts" / "hydra"
BATCHES_DIR = PROMPTS_DIR / "batches"
BATCHES_DIR.mkdir(parents=True, exist_ok=True)

KERNEL_LEMMAS = [
    "i", "you", "people", "someone", "something", "body", "kind", "part",
    "this", "same", "other", "one", "two", "some", "all", "much", "little",
    "good", "bad", "big", "small", "think", "know", "want", "dont-want",
    "feel", "see", "hear", "say", "words", "true", "do", "happen", "move",
    "touch", "be-somewhere", "there-is", "be", "mine", "live", "die", "when",
    "now", "before", "after", "a-long-time", "a-short-time", "for-some-time",
    "moment", "where", "here", "above", "below", "far", "near", "side",
    "inside", "not", "maybe", "can", "because", "if", "very", "more", "like",
    "water", "earth", "air", "fire", "stone", "wood", "creature", "animal",
    "plant", "head", "face", "eye", "hand", "foot", "blood", "eat", "drink",
    "sleep", "stand", "sit", "walk", "run", "make", "put", "give", "take",
    "hold", "cut", "push", "pull", "fall", "grow", "sound", "light", "dark",
    "color", "warm", "cold", "smell", "hard", "soft", "heavy", "fast",
    "slow", "clean", "round", "straight", "open", "home", "land", "sky",
    "sun", "end", "front", "back"
]

STUB_T1 = {
    "NAME(x)", "PERSON(x)", "LOCATION(x)", "NOUN(x)",
    "ADJECTIVE(x)", "ACTION(x)", "PRED(x)", "SUBSTANCE(x)", "VERB(x)"
}

def clean_json_response(raw_text: str):
    text = raw_text.strip()
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence_match:
        text = fence_match.group(1).strip()
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        text = text[start:end+1]
    return json.loads(text)

def call_hydra_free(prompt: str, system_prompt: str, max_tokens: int = 4096) -> str:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [
        sys.executable, "-m", "hydra_cli.cli", "free",
        "--system", system_prompt,
        "--no-stream",
        "--max-tokens", str(max_tokens),
        "--", prompt
    ]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(ROOT),
        env=env,
        timeout=120
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Hydra CLI failed (code {proc.returncode}): {proc.stderr}")
    return proc.stdout.strip()

def select_candidate_batch(batch_num: int = 1, batch_size: int = 10):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    
    cur.execute("""
    SELECT id, lemma, pos, gloss, dewey, t1_decomposition, depth
    FROM nodes
    ORDER BY id ASC
    """)
    rows = cur.fetchall()
    
    candidates = []
    for r in rows:
        node_id, lemma, pos, gloss, dewey, t1, depth = r
        words = (gloss or "").split()
        if t1 in STUB_T1 or dewey == "813.54" or len(words) < 8:
            cur.execute("""
            SELECT relation, target_lemma, weight
            FROM edges
            WHERE source_id = ?
            """, (node_id,))
            edge_rows = cur.fetchall()
            edges = [{"rel": er[0], "target": er[1], "weight": er[2]} for er in edge_rows]
            
            candidates.append({
                "id": node_id,
                "lemma": lemma,
                "pos": pos,
                "gloss": gloss,
                "dewey": dewey,
                "t1_decomposition": t1,
                "depth": depth,
                "edges": edges
            })
    
    con.close()
    
    offset = (batch_num - 1) * batch_size
    batch = candidates[offset:offset + batch_size]
    return batch

def run_batch(batch_num: int = 1):
    batch_name = f"sense-{batch_num:04d}"
    print(f"[*] Preparing batch {batch_name}...")
    
    batch_items = select_candidate_batch(batch_num, 10)
    if not batch_items:
        print("[!] No candidate items found for batch.")
        return
    
    json_path = BATCHES_DIR / f"{batch_name}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(batch_items, f, indent=2)
    print(f"[+] Saved input slice: {json_path}")
    
    with open(PROMPTS_DIR / "00-system.md", "r", encoding="utf-8") as f:
        system_prompt = f.read()
        
    with open(PROMPTS_DIR / "01-sense-repair.md", "r", encoding="utf-8") as f:
        repair_template = f.read()
        
    prompt_text = repair_template.replace("{{ROWS_JSON}}", json.dumps(batch_items, indent=2))
    prompt_file = BATCHES_DIR / f"{batch_name}.prompt.md"
    with open(prompt_file, "w", encoding="utf-8") as f:
        f.write(prompt_text)
    print(f"[+] Saved repair prompt: {prompt_file}")
    
    raw_file = BATCHES_DIR / f"{batch_name}.raw.txt"
    if raw_file.exists() and raw_file.stat().st_size > 50:
        print(f"[*] Using existing raw repair response: {raw_file}")
        with open(raw_file, "r", encoding="utf-8") as f:
            raw_repair = f.read()
    else:
        print(f"[*] Summoning Hydra Free for sense repair...")
        raw_repair = call_hydra_free(prompt_text, system_prompt, max_tokens=4096)
        with open(raw_file, "w", encoding="utf-8") as f:
            f.write(raw_repair)
        print(f"[+] Saved raw response: {raw_file}")
    
    proposed_json = clean_json_response(raw_repair)
    print(f"[+] Successfully parsed {len(proposed_json)} proposed rows.")
        
    with open(PROMPTS_DIR / "03-audit.md", "r", encoding="utf-8") as f:
        audit_template = f.read()
        
    batch_lemmas = [item["lemma"] for item in batch_items]
    allow_list = sorted(list(set(KERNEL_LEMMAS + batch_lemmas)))
    
    audit_prompt = audit_template.replace(
        "{{ALLOW_JSON}}", json.dumps(allow_list)
    ).replace(
        "{{INPUT_JSON}}", json.dumps(batch_items, indent=2)
    ).replace(
        "{{PROPOSED_JSON}}", json.dumps(proposed_json, indent=2)
    )
    
    audit_prompt_file = BATCHES_DIR / f"{batch_name}.audit.md"
    with open(audit_prompt_file, "w", encoding="utf-8") as f:
        f.write(audit_prompt)
    print(f"[+] Saved audit prompt: {audit_prompt_file}")
    
    audit_file = BATCHES_DIR / f"{batch_name}.audit.txt"
    if audit_file.exists() and audit_file.stat().st_size > 50:
        print(f"[*] Using existing raw audit response: {audit_file}")
        with open(audit_file, "r", encoding="utf-8") as f:
            raw_audit = f.read()
    else:
        print(f"[*] Summoning Hydra Free for audit...")
        raw_audit = call_hydra_free(audit_prompt, system_prompt, max_tokens=2048)
        with open(audit_file, "w", encoding="utf-8") as f:
            f.write(raw_audit)
        print(f"[+] Saved raw audit: {audit_file}")
    
    audit_json = clean_json_response(raw_audit)
    print(f"[+] Successfully parsed {len(audit_json)} audit verdicts.")

    # Step 4: Write back
    print(f"[*] Processing writeback for accepted rows...")
    proposed_map = {row["lemma"]: row for row in proposed_json if "lemma" in row}
    
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    
    accepted_count = 0
    rejected_count = 0
    
    for audit_entry in audit_json:
        lemma = audit_entry.get("lemma")
        verdict = audit_entry.get("verdict")
        reasons = audit_entry.get("reasons", [])
        
        if verdict == "accept" and lemma in proposed_map:
            prop = proposed_map[lemma]
            new_gloss = prop.get("gloss")
            new_dewey = str(prop.get("dewey"))
            new_t1 = prop.get("t1_decomposition")
            new_depth = int(prop.get("depth", 1))
            
            cur.execute("""
            UPDATE nodes
            SET gloss = ?, dewey = ?, t1_decomposition = ?, depth = ?
            WHERE lemma = ?
            """, (new_gloss, new_dewey, new_t1, new_depth, lemma))
            
            accepted_count += 1
            safe_lemma = lemma.encode("ascii", "replace").decode("ascii")
            print(f"  [ACCEPT] {safe_lemma}: dewey={new_dewey}, t1={new_t1}, depth={new_depth}")
        else:
            rejected_count += 1
            safe_lemma = str(lemma).encode("ascii", "replace").decode("ascii")
            print(f"  [REJECT] {safe_lemma}: reasons={reasons}")
            
    con.commit()
    con.close()
    
    print(f"[+] Batch {batch_name} complete: {accepted_count} accepted, {rejected_count} rejected.")

if __name__ == "__main__":
    run_batch(1)
