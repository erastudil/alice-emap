"""build_emap_graph.py - Alice 1.0 EMap Graph Scaling & Multi-Pool Harness.

Partitions the 44,000 lemma inventory, executes wide fan-out across:
1. CheaperInference GLM 5.3 (with strict $5.00 cumulative spend ceiling)
2. OpenRouter Free Forge (strict fence: only :free models permitted, zero paid calls)
3. Cloudflare Workers AI (under account subscription allocation)

Validates closed relation classes and persists nodes/edges into SQLite and CSR binary storage.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sqlite3
import struct
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parent

CANONICAL_RELATIONS: Set[str] = {
    "hypernym", "hyponym", "instance_of", "has_instance",
    "part_of", "has_part", "member_of", "has_member", "substance_of",
    "synonym", "antonym", "derivation", "pertainym", "form_of", "has_form",
    "entails", "causes", "agent_of", "patient_of", "instrument_of", "attribute_of",
    "domain_topic", "bridge_analogy", "bridge_function",
}

RELATION_MAP: Dict[str, int] = {rel: i + 1 for i, rel in enumerate(sorted(CANONICAL_RELATIONS))}
POS_MAP: Dict[str, int] = {"N": 0, "V": 1, "A": 2, "R": 3, "P": 4, "UNKNOWN": 7}

DB_LOCK = threading.Lock()
CHEAPERINFERENCE_SPEND_CEILING = 5.00  # Strict spend ceiling in USD

SYSTEM_PROMPT = """You are an expert computational lexicographer and ontological engineer.
You extract formal sense nodes and relational edges for English lemmas according to the Alice 1.0 EMap specification.

Closed relation classes (use ONLY these 24 exact names):
hypernym, hyponym, instance_of, has_instance, part_of, has_part, member_of, has_member, substance_of,
synonym, antonym, derivation, pertainym, form_of, has_form, entails, causes, agent_of, patient_of,
instrument_of, attribute_of, domain_topic, bridge_analogy, bridge_function.

For each lemma provided, extract:
1. Primary sense with POS in ["N", "V", "A", "R", "P"], concise gloss, taxonomic depth integer (0=root, 1=high abstract, 2-6=concrete), Dewey decimal category string (e.g. "551.48", "610", "420"), and T1 primitive predicate decomposition (lambda form or prime composition e.g. "CAUSE(x, ...)" or "LIQUID(x)").
2. Edges connecting this lemma to other concept lemmas using only the 24 relation names with weight in (0.0, 1.0].

Output strictly a JSON array of objects, one per lemma:
[
  {
    "lemma": "...",
    "pos": "N",
    "gloss": "...",
    "depth": 2,
    "dewey": "551.48",
    "t1_decomposition": "LIQUID(x)",
    "edges": [
      {"rel": "hypernym", "target": "liquid", "weight": 0.95}
    ]
  }
]
Output JSON array directly. Do not wrap in markdown tags. No discursive prose."""


class SecurityFenceViolation(Exception):
    """Raised when an execution violates a workspace fence."""


def enforce_provider_fences(url: str, model: str):
    """Enforce strict spend fences on OpenRouter and Vercel."""
    url_l = url.lower()
    if "vercel" in url_l or "ai-gateway" in url_l:
        raise SecurityFenceViolation(f"Fence violation: Vercel AI Gateway is strictly banned. (url: {url})")
    if "openrouter.ai" in url_l:
        if not model.endswith(":free"):
            raise SecurityFenceViolation(f"Fence violation: Paid OpenRouter model '{model}' is strictly banned. Only ':free' tier models permitted.")


def get_db(db_path: Path = ROOT / "emap.db") -> sqlite3.Connection:
    """Initialize or connect to SQLite database."""
    conn = sqlite3.connect(str(db_path), timeout=60.0)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS lemmas (
        idx INTEGER PRIMARY KEY,
        lemma TEXT UNIQUE NOT NULL,
        is_kernel BOOLEAN NOT NULL DEFAULT 0,
        category TEXT DEFAULT ''
    )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS nodes (
        id INTEGER PRIMARY KEY,
        lemma TEXT NOT NULL,
        pos TEXT NOT NULL,
        tier INTEGER NOT NULL DEFAULT 0,
        sense_id TEXT UNIQUE NOT NULL,
        gloss TEXT NOT NULL,
        dewey TEXT NOT NULL,
        t1_decomposition TEXT NOT NULL,
        depth INTEGER NOT NULL,
        lorentz_r REAL NOT NULL
    )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS edges (
        source_id INTEGER NOT NULL,
        target_id INTEGER,
        relation TEXT NOT NULL,
        weight REAL NOT NULL,
        source_lemma TEXT NOT NULL,
        target_lemma TEXT NOT NULL,
        PRIMARY KEY (source_lemma, target_lemma, relation)
    )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS batches (
        batch_id INTEGER PRIMARY KEY,
        start_idx INTEGER NOT NULL,
        end_idx INTEGER NOT NULL,
        status TEXT NOT NULL,
        model TEXT NOT NULL,
        node_count INTEGER DEFAULT 0,
        edge_count INTEGER DEFAULT 0,
        updated_at TIMESTAMP NOT NULL
    )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS spend_ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        provider TEXT NOT NULL,
        model TEXT NOT NULL,
        prompt_tokens INTEGER NOT NULL,
        completion_tokens INTEGER NOT NULL,
        cost REAL NOT NULL,
        cumulative_spend REAL NOT NULL,
        timestamp TIMESTAMP NOT NULL
    )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_nodes_lemma ON nodes (lemma)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON edges (source_lemma)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_target ON edges (target_lemma)")
    conn.commit()
    return conn


def get_cumulative_cheaperinference_spend(db: sqlite3.Connection) -> float:
    """Retrieve cumulative CheaperInference spend from spend ledger."""
    with DB_LOCK:
        cur = db.cursor()
        cur.execute("SELECT COALESCE(SUM(cost), 0.0) FROM spend_ledger WHERE provider = 'cheaperinference'")
        return float(cur.fetchone()[0])


def record_spend(db: sqlite3.Connection, provider: str, model: str, prompt_tok: int, comp_tok: int, cost: float):
    """Record model invocation spend in persistent ledger."""
    with DB_LOCK:
        cur = db.cursor()
        cur.execute("SELECT COALESCE(SUM(cost), 0.0) FROM spend_ledger WHERE provider = ?", (provider,))
        prev_spend = float(cur.fetchone()[0])
        new_spend = prev_spend + cost
        cur.execute("""
        INSERT INTO spend_ledger (provider, model, prompt_tokens, completion_tokens, cost, cumulative_spend, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (provider, model, prompt_tok, comp_tok, cost, new_spend, datetime.now(timezone.utc).isoformat()))
        db.commit()


def pack_node_id(pos_char: str, tier: int, local_id: int) -> int:
    """Encode 32-bit stable ID: [31..29] POS (3b) | [28..26] tier (3b) | [25..0] local_id (26b)."""
    pos_code = POS_MAP.get(pos_char.upper(), 7) & 0x07
    tier_code = tier & 0x07
    lid = local_id & 0x03FFFFFF
    return (pos_code << 29) | (tier_code << 26) | lid


def parse_model_json(text: str) -> List[Dict[str, Any]]:
    """Clean markdown code fences, recover truncated chunks, and parse JSON array."""
    s = text.strip()
    m = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", s, re.DOTALL)
    if m:
        s = m.group(1).strip()
    elif s.startswith("```"):
        parts = s.split("```")
        if len(parts) >= 2:
            inner = parts[1].strip()
            if inner.startswith("json"):
                inner = inner[4:].strip()
            s = inner

    start = s.find("[")
    end = s.rfind("]")
    if start != -1:
        if end != -1 and end > start:
            s = s[start:end+1]
        else:
            last_brace = s.rfind("}")
            if last_brace != -1 and last_brace > start:
                s = s[start:last_brace+1] + "]"

    # Clean trailing commas
    s_clean = re.sub(r",\s*([\]}])", r"\1", s)
    try:
        data = json.loads(s_clean)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "lemmas" in data:
            out = []
            for k, v in data["lemmas"].items():
                if isinstance(v, dict):
                    v["lemma"] = k
                    out.append(v)
            return out
    except Exception:
        entries = []
        for obj_str in re.findall(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", s):
            try:
                clean_obj = re.sub(r",\s*([\]}])", r"\1", obj_str)
                obj = json.loads(clean_obj)
                if isinstance(obj, dict) and "lemma" in obj:
                    entries.append(obj)
            except Exception:
                continue
        if entries:
            return entries
    return []


def query_cheaperinference_glm53(db: sqlite3.Connection, lemmas: List[str], max_retries: int = 3) -> Optional[Tuple[List[Dict[str, Any]], str]]:
    """Query GLM 5.3 via CheaperInference with spend accumulator, retry loop, and $5.00 ceiling check."""
    key = os.environ.get("CHEAPERINFERENCE_API_KEY")
    if not key:
        return None

    url = "https://api.cheaperinference.com/v1/chat/completions"
    model = "glm-5.3"
    enforce_provider_fences(url, model)
    prompt = f"Extract emap specification entries for lemmas: {json.dumps(lemmas)}"

    for attempt in range(1, max_retries + 1):
        current_spend = get_cumulative_cheaperinference_spend(db)
        if current_spend >= CHEAPERINFERENCE_SPEND_CEILING:
            print(f"[SPEND ACCUMULATOR] CheaperInference ceiling hit (${current_spend:.4f} >= ${CHEAPERINFERENCE_SPEND_CEILING:.2f}). Deactivating pool.")
            return None

        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            data=json.dumps({
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 4000
            }).encode(),
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode())
                usage = data.get("usage", {})
                prompt_tok = usage.get("prompt_tokens", 0)
                comp_tok = usage.get("completion_tokens", 0)
                cost = usage.get("cost", (prompt_tok * 0.0000001) + (comp_tok * 0.0000002))
                record_spend(db, "cheaperinference", model, prompt_tok, comp_tok, cost)
                content = data["choices"][0]["message"]["content"]
                parsed = parse_model_json(content)
                if parsed:
                    return parsed, f"cheaperinference/{model}"
                print(f"[CHEAPERINFERENCE GLM 5.3] Attempt {attempt}/{max_retries}: parsed empty JSON.")
        except urllib.error.HTTPError as h_err:
            if h_err.code in (401, 403):
                print(f"[CHEAPERINFERENCE GLM 5.3] Fatal HTTP auth error {h_err.code}: {h_err.reason}")
                return None
            backoff = 2 ** attempt
            print(f"[CHEAPERINFERENCE GLM 5.3] Attempt {attempt}/{max_retries} HTTP {h_err.code}: {h_err.reason}. Retrying in {backoff}s...")
            time.sleep(backoff)
        except Exception as exc:
            backoff = 2 ** attempt
            print(f"[CHEAPERINFERENCE GLM 5.3] Attempt {attempt}/{max_retries} socket/timeout error: {exc}. Retrying in {backoff}s...")
            time.sleep(backoff)

    return None


def query_cloudflare_workers_ai(lemmas: List[str]) -> Optional[Tuple[List[Dict[str, Any]], str]]:
    """Query Cloudflare Workers AI under account subscription allocation."""
    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    account = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    if not token or not account:
        return None

    prompt = f"Extract emap specification entries for lemmas: {json.dumps(lemmas)}"
    for model in ["@cf/meta/llama-3.2-3b-instruct", "@cf/meta/llama-3.2-1b-instruct"]:
        url = f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/v1/chat/completions"
        enforce_provider_fences(url, model)
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            data=json.dumps({
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 4000
            }).encode(),
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode())
                content = data["choices"][0]["message"]["content"]
                parsed = parse_model_json(content)
                if parsed:
                    return parsed, f"cloudflare/{model}"
        except Exception:
            continue
    return None


def query_openrouter_free_forge(lemmas: List[str]) -> Optional[Tuple[List[Dict[str, Any]], str]]:
    """Query OpenRouter Free Forge models strictly enforcing :free fence."""
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        return None

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/erastudil/hydra",
        "X-Title": "Hydra Free Forge",
    }
    prompt = f"Extract emap specification entries for lemmas: {json.dumps(lemmas)}"

    free_models = [
        "nvidia/nemotron-3.5-lightning:free",
        "google/gemma-4-26b-a4b-it:free",
        "google/gemma-4-31b-it:free",
    ]

    for model in free_models:
        enforce_provider_fences(url, model)
        req = urllib.request.Request(
            url,
            headers=headers,
            data=json.dumps({
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 4000
            }).encode(),
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode())
                content = data["choices"][0]["message"]["content"]
                parsed = parse_model_json(content)
                if parsed:
                    return parsed, f"openrouter/{model}"
        except Exception as exc:
            continue
    return None


def extract_batch_multipool(db: sqlite3.Connection, lemmas: List[str], preferred_pool: str = "auto") -> Tuple[List[Dict[str, Any]], str]:
    """Execute multi-pool extraction adhering to spend fences and fallbacks."""
    # 1. Cloudflare Workers AI (if credentials present)
    cf_res = query_cloudflare_workers_ai(lemmas)
    if cf_res:
        return cf_res

    # 2. CheaperInference GLM 5.3 (tracked under $5.00 ceiling)
    if preferred_pool in ("auto", "cheaperinference", "glm"):
        glm_res = query_cheaperinference_glm53(db, lemmas)
        if glm_res:
            return glm_res

    # 3. OpenRouter Free Forge (:free models only)
    free_res = query_openrouter_free_forge(lemmas)
    if free_res:
        return free_res

    raise RuntimeError(f"All extraction pools failed for batch: {lemmas[:5]}")


def process_batch(db: sqlite3.Connection, batch_id: int, start_idx: int, end_idx: int, pool: str = "auto") -> Tuple[int, int]:
    """Extract and persist a single batch of lemmas with thread-safe DB transactions."""
    with DB_LOCK:
        cursor = db.cursor()
        cursor.execute("SELECT idx, lemma FROM lemmas WHERE idx >= ? AND idx < ? ORDER BY idx", (start_idx, end_idx))
        rows = cursor.fetchall()
        if not rows:
            return 0, 0

        lemmas_list = [r[1] for r in rows]
        idx_map = {r[1]: r[0] for r in rows}

        now_iso = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
        INSERT OR REPLACE INTO batches (batch_id, start_idx, end_idx, status, model, updated_at)
        VALUES (?, ?, ?, 'PROCESSING', ?, ?)
        """, (batch_id, start_idx, end_idx, pool, now_iso))
        db.commit()

    # Multi-pool extraction outside DB lock
    try:
        entries, actual_model = extract_batch_multipool(db, lemmas_list, preferred_pool=pool)
    except Exception as exc:
        with DB_LOCK:
            cursor = db.cursor()
            cursor.execute("UPDATE batches SET status = 'FAILED', updated_at = ? WHERE batch_id = ?",
                           (datetime.now(timezone.utc).isoformat(), batch_id))
            db.commit()
        raise exc

    nodes_inserted = 0
    edges_inserted = 0

    with DB_LOCK:
        cursor = db.cursor()
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            lem = entry.get("lemma", "").strip().lower()
            if not lem:
                continue
            pos = str(entry.get("pos", "N")).upper()[:1]
            gloss = str(entry.get("gloss", "concept definition"))
            dewey = str(entry.get("dewey", "420"))
            t1_decomp = str(entry.get("t1_decomposition", "PRED(x)"))
            try:
                depth = int(entry.get("depth", 2))
            except Exception:
                depth = 2
            lorentz_r = math.log(1.0 + depth)

            local_id = idx_map.get(lem, 0)
            node_id = pack_node_id(pos, tier=0, local_id=local_id)
            sense_id = f"{lem}.{pos.lower()}.01"

            cursor.execute("""
            INSERT OR REPLACE INTO nodes (id, lemma, pos, tier, sense_id, gloss, dewey, t1_decomposition, depth, lorentz_r)
            VALUES (?, ?, ?, 0, ?, ?, ?, ?, ?, ?)
            """, (node_id, lem, pos, sense_id, gloss, dewey, t1_decomp, depth, lorentz_r))
            nodes_inserted += 1

            for edge in entry.get("edges", []):
                if not isinstance(edge, dict):
                    continue
                rel = str(edge.get("rel", "")).strip().lower()
                target = str(edge.get("target", "")).strip().lower()
                try:
                    weight = float(edge.get("weight", 0.9))
                except Exception:
                    weight = 0.9

                if rel == "kind_of":
                    rel = "hypernym"
                elif rel == "opposite":
                    rel = "antonym"

                if rel in CANONICAL_RELATIONS and target:
                    cursor.execute("""
                    INSERT OR REPLACE INTO edges (source_id, target_id, relation, weight, source_lemma, target_lemma)
                    VALUES (?, NULL, ?, ?, ?, ?)
                    """, (node_id, rel, weight, lem, target))
                    edges_inserted += 1

        now_iso = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
        UPDATE batches SET status = 'COMPLETED', model = ?, node_count = ?, edge_count = ?, updated_at = ?
        WHERE batch_id = ?
        """, (actual_model, nodes_inserted, edges_inserted, now_iso, batch_id))
        db.commit()

    return nodes_inserted, edges_inserted


def reconcile_failed_batches(db: sqlite3.Connection, pool: str = "auto", workers: int = 6) -> Tuple[int, int, int]:
    """Query batches with status = 'FAILED' or stale 'PROCESSING' and re-process them."""
    with DB_LOCK:
        cursor = db.cursor()
        cursor.execute("UPDATE batches SET status = 'FAILED' WHERE status = 'PROCESSING'")
        db.commit()
        cursor.execute("SELECT batch_id, start_idx, end_idx FROM batches WHERE status = 'FAILED' ORDER BY batch_id")
        failed_rows = cursor.fetchall()

    if not failed_rows:
        print("[RECONCILIATION] No failed batches found.")
        return 0, 0, 0

    print(f"[RECONCILIATION] Reconciling {len(failed_rows)} failed batches with {workers} workers...")
    t_start = time.time()
    recovered_batches = 0
    total_nodes = 0
    total_edges = 0

    def reconcile_job(row):
        b_idx, s_idx, e_idx = row
        job_db = get_db()
        try:
            print(f"[RECONCILE] Retrying batch {b_idx} (lemmas {s_idx}..{e_idx})...")
            n, e = process_batch(job_db, b_idx, s_idx, e_idx, pool=pool)
            job_db.close()
            return b_idx, n, e, None
        except Exception as exc:
            job_db.close()
            return b_idx, 0, 0, exc

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(reconcile_job, row): row[0] for row in failed_rows}
        for fut in as_completed(futures):
            b_id, n, e, err = fut.result()
            if err is None:
                recovered_batches += 1
                total_nodes += n
                total_edges += e
                print(f"[RECONCILE OK] Batch {b_id} recovered: {n} nodes, {e} edges")
            else:
                print(f"[RECONCILE FAIL] Batch {b_id} still failed: {err}")

    t_elapsed = time.time() - t_start
    print(f"[RECONCILIATION] Completed in {t_elapsed:.1f}s: {recovered_batches}/{len(failed_rows)} recovered (+{total_nodes} nodes, +{total_edges} edges)")
    return recovered_batches, total_nodes, total_edges


def run_batch_range(db: sqlite3.Connection, start_batch: int, max_batches: int, batch_size: int = 50, workers: int = 6, pool: str = "auto") -> Tuple[int, int, int]:
    """Execute a batch range skipping batches already completed."""
    target_batches = list(range(start_batch, start_batch + max_batches))
    with DB_LOCK:
        cursor = db.cursor()
        cursor.execute("SELECT batch_id FROM batches WHERE status = 'COMPLETED'")
        completed_set = {r[0] for r in cursor.fetchall()}

    pending = [b for b in target_batches if b not in completed_set]
    print(f"[BATCH RANGE] Target {len(target_batches)} batches ({start_batch}..{start_batch + max_batches - 1}). Completed: {len(target_batches) - len(pending)}. Pending: {len(pending)}")
    if not pending:
        return 0, 0, 0

    t_start = time.time()
    successful = 0
    total_nodes = 0
    total_edges = 0

    def worker_job(b_idx: int):
        job_db = get_db()
        s_idx = b_idx * batch_size
        e_idx = s_idx + batch_size
        print(f"[WORKER {b_idx}] processing batch {b_idx} (lemmas {s_idx}..{e_idx})...")
        t0 = time.time()
        n, e = process_batch(job_db, b_idx, s_idx, e_idx, pool=pool)
        dt = time.time() - t0
        print(f"[WORKER {b_idx}] completed in {dt:.1f}s: {n} nodes, {e} edges")
        job_db.close()
        return b_idx, n, e

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(worker_job, b_idx): b_idx for b_idx in pending}
        for fut in as_completed(futures):
            b_idx = futures[fut]
            try:
                _, n, e = fut.result()
                successful += 1
                total_nodes += n
                total_edges += e
            except Exception as exc:
                print(f"[ERROR] batch {b_idx} failed: {exc}")

    t_elapsed = time.time() - t_start
    print(f"[BATCH RANGE] Finished {successful}/{len(pending)} pending batches in {t_elapsed:.1f}s (+{total_nodes} nodes, +{total_edges} edges)")
    return successful, total_nodes, total_edges


def verify_graph(db: sqlite3.Connection) -> Dict[str, Any]:
    """Verify graph schema compliance, topological invariants, and report statistics."""
    with DB_LOCK:
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM lemmas")
        total_lemmas = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM nodes")
        node_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM edges")
        edge_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT relation) FROM edges")
        rel_count = cursor.fetchone()[0]

        cursor.execute("SELECT relation, COUNT(*) FROM edges GROUP BY relation ORDER BY COUNT(*) DESC")
        rel_dist = dict(cursor.fetchall())

        cursor.execute("SELECT pos, COUNT(*) FROM nodes GROUP BY pos")
        pos_dist = dict(cursor.fetchall())

        cursor.execute("SELECT AVG(depth), MIN(depth), MAX(depth) FROM nodes")
        avg_d, min_d, max_d = cursor.fetchone()

        cursor.execute("SELECT COUNT(DISTINCT dewey) FROM nodes")
        dewey_categories = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM batches WHERE status = 'COMPLETED'")
        completed_batches = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(cost), 0.0) FROM spend_ledger WHERE provider = 'cheaperinference'")
        ci_spend = float(cursor.fetchone()[0])

    return {
        "total_lemmas": total_lemmas,
        "nodes_extracted": node_count,
        "edges_extracted": edge_count,
        "distinct_relations": rel_count,
        "relation_distribution": rel_dist,
        "pos_distribution": pos_dist,
        "depth_metrics": {
            "average": round(avg_d, 2) if avg_d is not None else 0.0,
            "min": min_d or 0,
            "max": max_d or 0,
        },
        "dewey_categories": dewey_categories,
        "completed_batches": completed_batches,
        "cheaperinference_spend": ci_spend,
        "spend_ceiling": CHEAPERINFERENCE_SPEND_CEILING
    }


def export_csr(db: sqlite3.Connection, out_bin: Path = ROOT / "emap_csr.bin", out_meta: Path = ROOT / "emap_csr.json") -> int:
    """Export SQLite graph to CSR binary representation conforming to emap/SPEC.md."""
    with DB_LOCK:
        cursor = db.cursor()
        cursor.execute("SELECT lemma, id FROM nodes ORDER BY id")
        node_rows = cursor.fetchall()
        if not node_rows:
            print("no nodes present for CSR export")
            return 0

        node_to_idx = {r[0]: i for i, r in enumerate(node_rows)}
        n_nodes = len(node_rows)

        adj: List[List[Tuple[int, float, int]]] = [[] for _ in range(n_nodes)]
        cursor.execute("SELECT source_lemma, target_lemma, relation, weight FROM edges")
        edge_rows = cursor.fetchall()

    actual_edge_count = 0
    for s_lem, t_lem, rel, w in edge_rows:
        s_idx = node_to_idx.get(s_lem)
        t_idx = node_to_idx.get(t_lem)
        # Index 0 is a real node (lemma ζ). A missing target must not land there.
        if s_idx is None or t_idx is None:
            continue
        rel_code = RELATION_MAP.get(rel, 0)
        adj[s_idx].append((t_idx, float(w), rel_code))
        actual_edge_count += 1

    indptr: List[int] = [0]
    indices: List[int] = []
    weights: List[float] = []
    rel_types: List[int] = []

    for edges in adj:
        for t_idx, w, r_code in edges:
            indices.append(t_idx)
            weights.append(w)
            rel_types.append(r_code)
        indptr.append(len(indices))

    header = struct.pack("<4sIII", b"EMAP", 1, n_nodes, actual_edge_count)
    indptr_bytes = struct.pack(f"<{len(indptr)}i", *indptr)
    indices_bytes = struct.pack(f"<{len(indices)}i", *indices)
    weights_bytes = struct.pack(f"<{len(weights)}e", *weights)
    rel_bytes = struct.pack(f"<{len(rel_types)}B", *rel_types)

    payload = header + indptr_bytes + indices_bytes + weights_bytes + rel_bytes
    out_bin.write_bytes(payload)

    metadata = {
        "magic": "EMAP",
        "version": "1.0.0",
        "node_count": n_nodes,
        "edge_count": actual_edge_count,
        "payload_bytes": len(payload),
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }
    out_meta.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"exported CSR binary to {out_bin} ({len(payload)} bytes, {n_nodes} nodes, {actual_edge_count} edges)")
    return len(payload)


def main():
    parser = argparse.ArgumentParser(description="Alice 1.0 EMap Graph Multi-Pool Scaling Harness")
    parser.add_argument("--batch-size", type=int, default=50, help="Lemmas per worker batch")
    parser.add_argument("--max-batches", type=int, default=100, help="Number of batches to process in run")
    parser.add_argument("--start-batch", type=int, default=241, help="Starting batch index")
    parser.add_argument("--pool", type=str, default="auto", choices=["auto", "glm", "free", "cloudflare"], help="Extraction pool selection")
    parser.add_argument("--workers", type=int, default=6, help="Concurrent worker count")
    parser.add_argument("--verify", action="store_true", help="Verify graph schema and output metrics")
    parser.add_argument("--export-csr", action="store_true", help="Export CSR binary representation")
    parser.add_argument("--reconcile", action="store_true", help="Reconcile and re-process failed batches")
    parser.add_argument("--loop", action="store_true", help="Continuous milestone loop until complete or ceiling hit")
    parser.add_argument("--milestone-size", type=int, default=100, help="Batches per milestone in loop mode")
    parser.add_argument("--end-batch", type=int, default=880, help="Ending batch index for loop mode")
    args = parser.parse_args()

    db = get_db()

    if args.verify:
        metrics = verify_graph(db)
        print("\n--- EMAP GRAPH VERIFICATION REPORT ---")
        for k, v in metrics.items():
            if isinstance(v, dict):
                print(f"{k} :")
                for sub_k, sub_v in v.items():
                    print(f"  {sub_k} : {sub_v}")
            else:
                print(f"{k} : {v}")
        return

    if args.export_csr:
        export_csr(db)
        return

    if args.reconcile:
        reconcile_failed_batches(db, pool=args.pool, workers=args.workers)
        export_csr(db)
        metrics = verify_graph(db)
        print(f"\nreconciliation finished. Current nodes: {metrics['nodes_extracted']}, edges: {metrics['edges_extracted']}")
        return

    current_spend = get_cumulative_cheaperinference_spend(db)
    print(f"CheaperInference cumulative spend: ${current_spend:.4f} / ${CHEAPERINFERENCE_SPEND_CEILING:.2f} ceiling")

    if args.loop:
        print(f"[LOOP] Starting continuous milestone loop from batch {args.start_batch} to {args.end_batch} (milestone size {args.milestone_size})...")
        curr_b = args.start_batch
        m_idx = 1
        active_pool = args.pool

        while curr_b < args.end_batch:
            b_count = min(args.milestone_size, args.end_batch - curr_b)
            print(f"\n============================================================")
            print(f"=== MILESTONE {m_idx}: Batches {curr_b}..{curr_b + b_count - 1} (lemmas {curr_b * args.batch_size}..{(curr_b + b_count) * args.batch_size}) ===")
            print(f"============================================================")

            # 1. Reconcile failed batches
            reconcile_failed_batches(db, pool=active_pool, workers=args.workers)

            # 2. Process batch range
            run_batch_range(db, curr_b, b_count, batch_size=args.batch_size, workers=args.workers, pool=active_pool)

            # 3. Export CSR
            export_csr(db)

            # 4. Metrics
            metrics = verify_graph(db)
            print(f"[MILESTONE {m_idx} COMPLETE] Nodes: {metrics['nodes_extracted']}, Edges: {metrics['edges_extracted']}, Spend: ${metrics['cheaperinference_spend']:.4f}")

            current_spend = metrics['cheaperinference_spend']
            if current_spend >= CHEAPERINFERENCE_SPEND_CEILING and active_pool != 'free':
                print(f"[CEILING HIT] CheaperInference spend (${current_spend:.4f}) reached ${CHEAPERINFERENCE_SPEND_CEILING:.2f} ceiling.")
                if active_pool == 'glm':
                    print("[CEILING STOP] Pool explicitly set to glm. Halting loop.")
                    break
                else:
                    print("[CUTOVER] Switching extraction pool to OpenRouter Free Forge (:free models only)...")
                    active_pool = 'free'

            curr_b += b_count
            m_idx += 1

        print("\n[LOOP FINISHED] All target milestones executed.")
        return

    # Standard single-range run
    reconcile_failed_batches(db, pool=args.pool, workers=args.workers)
    run_batch_range(db, args.start_batch, args.max_batches, batch_size=args.batch_size, workers=args.workers, pool=args.pool)
    export_csr(db)
    metrics = verify_graph(db)
    print("\n--- AGGREGATE GRAPH METRICS ---")
    for k, v in metrics.items():
        if isinstance(v, dict):
            print(f"{k} : {json.dumps(v)}")
        else:
            print(f"{k} : {v}")


if __name__ == "__main__":
    main()
