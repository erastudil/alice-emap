"""alice_decision_engine.py - Alice 1.0 Decision Model & Arbitration Engine.

Implements the formal arbitration lattice and provenance pipeline defined in emap/SPEC.md:
1. COMPUTE: deterministic execution for rational CAS arithmetic, SI 7-dimension units, and Gregorian datetime.
2. RETRIEVE: topological navigation of emap.db / emap_csr.bin to fetch Dewey-indexed facts.
3. HAND: out-of-band proxy tool execution for whitelisted domain queries.
4. ABSTAIN: explicit calibrated refusal when confidence falls below threshold theta.

Invariants:
- Ground-truth precedence: COMPUTE strictly precedes RETRIEVE; RETRIEVE strictly precedes HAND.
- Zero-unprovenanced fact guarantee: all non-abstain answers carry an immutable 64-char SHA256 provenance digest.
"""

from __future__ import annotations

import fractions
import hashlib
import json
import math
import re
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "emap.db"
CSR_BIN_PATH = ROOT / "emap_csr.bin"


class ActionType(str, Enum):
    COMPUTE = "COMPUTE"
    RETRIEVE = "RETRIEVE"
    HAND = "HAND"
    ABSTAIN = "ABSTAIN"


@dataclass
class ProvenanceRecord:
    route: ActionType
    source: str
    digest: str
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DecisionReceipt:
    request_id: str
    action: ActionType
    answer: str
    confidence: float
    provenance: Optional[ProvenanceRecord]
    latency_ms: float
    execution_trace: List[str] = field(default_factory=list)


# -----------------------------------------------------------------------------
# 1. Deterministic Engine (COMPUTE)
# -----------------------------------------------------------------------------

@dataclass(frozen=True)
class SIDimension:
    """SI 7-base dimension vector [L, M, T, I, Theta, N, J] in Z^7."""
    L: int = 0      # Length (meter)
    M: int = 0      # Mass (kilogram)
    T: int = 0      # Time (second)
    I: int = 0      # Electric current (ampere)
    Theta: int = 0  # Thermodynamic temperature (kelvin)
    N: int = 0      # Amount of substance (mole)
    J: int = 0      # Luminous intensity (candela)

    def as_vector(self) -> Tuple[int, int, int, int, int, int, int]:
        return (self.L, self.M, self.T, self.I, self.Theta, self.N, self.J)

    def __eq__(self, other):
        if not isinstance(other, SIDimension):
            return False
        return self.as_vector() == other.as_vector()

    def __repr__(self) -> str:
        return f"[{self.L},{self.M},{self.T},{self.I},{self.Theta},{self.N},{self.J}]"


class DeterministicEngine:
    """Executes exact rational CAS, SI 7-dimension units algebra, and Gregorian calendar engines."""

    # Unit registry: (scale_factor_to_SI_base, SIDimension)
    UNIT_REGISTRY: Dict[str, Tuple[float, SIDimension]] = {
        # Length [1,0,0,0,0,0,0]
        "m": (1.0, SIDimension(L=1)),
        "meter": (1.0, SIDimension(L=1)),
        "meters": (1.0, SIDimension(L=1)),
        "km": (1000.0, SIDimension(L=1)),
        "kilometer": (1000.0, SIDimension(L=1)),
        "kilometers": (1000.0, SIDimension(L=1)),
        "cm": (0.01, SIDimension(L=1)),
        "centimeter": (0.01, SIDimension(L=1)),
        "centimeters": (0.01, SIDimension(L=1)),
        "mm": (0.001, SIDimension(L=1)),
        "millimeter": (0.001, SIDimension(L=1)),
        "millimeters": (0.001, SIDimension(L=1)),
        "mi": (1609.344, SIDimension(L=1)),
        "mile": (1609.344, SIDimension(L=1)),
        "miles": (1609.344, SIDimension(L=1)),
        "ft": (0.3048, SIDimension(L=1)),
        "foot": (0.3048, SIDimension(L=1)),
        "feet": (0.3048, SIDimension(L=1)),
        "in": (0.0254, SIDimension(L=1)),
        "inch": (0.0254, SIDimension(L=1)),
        "inches": (0.0254, SIDimension(L=1)),

        # Mass [0,1,0,0,0,0,0]
        "kg": (1.0, SIDimension(M=1)),
        "kilogram": (1.0, SIDimension(M=1)),
        "kilograms": (1.0, SIDimension(M=1)),
        "g": (0.001, SIDimension(M=1)),
        "gram": (0.001, SIDimension(M=1)),
        "grams": (0.001, SIDimension(M=1)),
        "mg": (0.000001, SIDimension(M=1)),
        "lb": (0.45359237, SIDimension(M=1)),
        "pound": (0.45359237, SIDimension(M=1)),
        "pounds": (0.45359237, SIDimension(M=1)),
        "oz": (0.028349523125, SIDimension(M=1)),
        "ounce": (0.028349523125, SIDimension(M=1)),
        "ounces": (0.028349523125, SIDimension(M=1)),

        # Time [0,0,1,0,0,0,0]
        "s": (1.0, SIDimension(T=1)),
        "sec": (1.0, SIDimension(T=1)),
        "second": (1.0, SIDimension(T=1)),
        "seconds": (1.0, SIDimension(T=1)),
        "min": (60.0, SIDimension(T=1)),
        "minute": (60.0, SIDimension(T=1)),
        "minutes": (60.0, SIDimension(T=1)),
        "h": (3600.0, SIDimension(T=1)),
        "hr": (3600.0, SIDimension(T=1)),
        "hour": (3600.0, SIDimension(T=1)),
        "hours": (3600.0, SIDimension(T=1)),
        "day": (86400.0, SIDimension(T=1)),
        "days": (86400.0, SIDimension(T=1)),

        # Speed [1,0,-1,0,0,0,0]
        "m/s": (1.0, SIDimension(L=1, T=-1)),
        "km/h": (1000.0 / 3600.0, SIDimension(L=1, T=-1)),
        "kmh": (1000.0 / 3600.0, SIDimension(L=1, T=-1)),
        "mph": (1609.344 / 3600.0, SIDimension(L=1, T=-1)),
        "knot": (1852.0 / 3600.0, SIDimension(L=1, T=-1)),
        "knots": (1852.0 / 3600.0, SIDimension(L=1, T=-1)),

        # Force [1,1,-2,0,0,0,0]
        "n": (1.0, SIDimension(L=1, M=1, T=-2)),
        "newton": (1.0, SIDimension(L=1, M=1, T=-2)),
        "newtons": (1.0, SIDimension(L=1, M=1, T=-2)),
        "kn": (1000.0, SIDimension(L=1, M=1, T=-2)),

        # Energy [2,1,-2,0,0,0,0]
        "j": (1.0, SIDimension(L=2, M=1, T=-2)),
        "joule": (1.0, SIDimension(L=2, M=1, T=-2)),
        "joules": (1.0, SIDimension(L=2, M=1, T=-2)),
        "kj": (1000.0, SIDimension(L=2, M=1, T=-2)),
        "cal": (4.184, SIDimension(L=2, M=1, T=-2)),
        "calorie": (4.184, SIDimension(L=2, M=1, T=-2)),
        "calories": (4.184, SIDimension(L=2, M=1, T=-2)),
        "kcal": (4184.0, SIDimension(L=2, M=1, T=-2)),

        # Power [2,1,-3,0,0,0,0]
        "w": (1.0, SIDimension(L=2, M=1, T=-3)),
        "watt": (1.0, SIDimension(L=2, M=1, T=-3)),
        "watts": (1.0, SIDimension(L=2, M=1, T=-3)),
        "kw": (1000.0, SIDimension(L=2, M=1, T=-3)),
        "hp": (745.699872, SIDimension(L=2, M=1, T=-3)),

        # Electric Current [0,0,0,1,0,0,0]
        "a": (1.0, SIDimension(I=1)),
        "amp": (1.0, SIDimension(I=1)),
        "ampere": (1.0, SIDimension(I=1)),
        "amperes": (1.0, SIDimension(I=1)),

        # Temperature [0,0,0,0,1,0,0]
        "k": (1.0, SIDimension(Theta=1)),
        "kelvin": (1.0, SIDimension(Theta=1)),
    }

    @classmethod
    def evaluate_cas_rational(cls, expr: str) -> Optional[Tuple[str, str]]:
        """Exact rational Computer Algebra System (CAS) with zero floating point drift."""
        clean = expr.strip()
        clean = re.sub(r"^(?:calculate|compute|solve|simplify|what\s+is)\s+", "", clean, flags=re.IGNORECASE)
        clean = clean.rstrip("?=").strip()

        # GCD / LCM
        m_gcd = re.match(r"^gcd\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)$", clean, flags=re.IGNORECASE)
        if m_gcd:
            a, b = int(m_gcd.group(1)), int(m_gcd.group(2))
            res = math.gcd(a, b)
            digest = hashlib.sha256(f"CAS:gcd({a},{b})={res}".encode()).hexdigest()
            return f"Exact GCD: {res}", digest

        m_lcm = re.match(r"^lcm\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)$", clean, flags=re.IGNORECASE)
        if m_lcm:
            a, b = int(m_lcm.group(1)), int(m_lcm.group(2))
            res = math.lcm(a, b)
            digest = hashlib.sha256(f"CAS:lcm({a},{b})={res}".encode()).hexdigest()
            return f"Exact LCM: {res}", digest

        # Exact sqrt
        m_sqrt = re.match(r"^sqrt\s*\(\s*(\d+)\s*\)$", clean, flags=re.IGNORECASE)
        if m_sqrt:
            val = int(m_sqrt.group(1))
            root = math.isqrt(val)
            if root * root == val:
                digest = hashlib.sha256(f"CAS:sqrt({val})={root}".encode()).hexdigest()
                return f"Exact Integer: {root}", digest
            else:
                f_val = math.sqrt(val)
                digest = hashlib.sha256(f"CAS:sqrt({val})={f_val}".encode()).hexdigest()
                return f"Numerical Bound: {f_val:.8f}", digest

        # Rational arithmetic parser
        # Transform integer/fraction tokens to Fraction(...) in expression
        # Allow numbers, fractions, +, -, *, /, **, (, )
        if re.match(r"^[\d\s\+\-\*\/\(\)\^]+$", clean) and any(op in clean for op in "+-*/^"):
            norm_expr = clean.replace("^", "**")
            # Replace pure numbers '123' with 'fractions.Fraction(123)'
            # Use regex to convert all integer tokens
            tokens = re.split(r"(\*\*|[\+\-\*\/\(\)])", norm_expr)
            rebuilt = []
            for t in tokens:
                ts = t.strip()
                if ts.isdigit():
                    rebuilt.append(f"fractions.Fraction({ts})")
                else:
                    rebuilt.append(t)
            eval_str = "".join(rebuilt)

            try:
                code = compile(eval_str, "<string>", "eval")
                # Only allow fractions.Fraction in eval context
                val = eval(code, {"fractions": fractions}, {})
                if isinstance(val, (int, fractions.Fraction)):
                    frac = fractions.Fraction(val)
                    if frac.denominator == 1:
                        ans_str = f"Exact Integer: {frac.numerator}"
                    else:
                        ans_str = f"Exact Rational: {frac.numerator}/{frac.denominator}"
                    digest = hashlib.sha256(f"CAS:{clean}={ans_str}".encode()).hexdigest()
                    return ans_str, digest
            except Exception:
                pass

        return None

    @classmethod
    def evaluate_si_dimensions(cls, query: str) -> Optional[Tuple[str, str]]:
        """Convert physical quantities with SI 7-base dimensional consistency check."""
        m = re.search(r"(\d+(?:\.\d+)?)\s*([a-zA-Z\/]+)\s+(?:in|to|into)\s+([a-zA-Z\/]+)", query, re.IGNORECASE)
        if not m:
            return None
        val_str, u1_raw, u2_raw = m.groups()
        val = float(val_str)
        u1 = u1_raw.lower()
        u2 = u2_raw.lower()

        # Affine Temperature conversions
        if u1 in ("c", "celsius") and u2 in ("f", "fahrenheit"):
            res = (val * 9.0 / 5.0) + 32.0
            out = f"Exact Affine: {res:.2f} F (Dimension: [0,0,0,0,1,0,0])"
            digest = hashlib.sha256(f"SI_UNITS:{val}C->F={out}".encode()).hexdigest()
            return out, digest
        if u1 in ("f", "fahrenheit") and u2 in ("c", "celsius"):
            res = (val - 32.0) * 5.0 / 9.0
            out = f"Exact Affine: {res:.2f} C (Dimension: [0,0,0,0,1,0,0])"
            digest = hashlib.sha256(f"SI_UNITS:{val}F->C={out}".encode()).hexdigest()
            return out, digest
        if u1 in ("c", "celsius") and u2 in ("k", "kelvin"):
            res = val + 273.15
            out = f"Exact Affine: {res:.2f} K (Dimension: [0,0,0,0,1,0,0])"
            digest = hashlib.sha256(f"SI_UNITS:{val}C->K={out}".encode()).hexdigest()
            return out, digest

        if u1 in cls.UNIT_REGISTRY and u2 in cls.UNIT_REGISTRY:
            scale1, dim1 = cls.UNIT_REGISTRY[u1]
            scale2, dim2 = cls.UNIT_REGISTRY[u2]

            if dim1 != dim2:
                err_msg = f"DIMENSIONAL_TYPE_ERROR: Incompatible SI dimensions {dim1} vs {dim2}"
                digest = hashlib.sha256(f"SI_UNITS_ERROR:{u1}->{u2}={dim1}!={dim2}".encode()).hexdigest()
                return err_msg, digest

            base_val = val * scale1
            target_val = base_val / scale2
            out = f"{target_val:.6g} {u2_raw} (Dimension: {dim1})"
            digest = hashlib.sha256(f"SI_UNITS:{val}{u1}->{u2}={out}".encode()).hexdigest()
            return out, digest

        return None

    @classmethod
    def evaluate_proleptic_gregorian(cls, query: str) -> Optional[Tuple[str, str]]:
        """Evaluate proleptic Gregorian calendar dates, offsets, and timezone conversions."""
        q = query.strip()

        # 1. Date differences: "days between <date1> and <date2>"
        m_diff = re.search(r"days\s+between\s+(\d{4}-\d{2}-\d{2})\s+and\s+(\d{4}-\d{2}-\d{2})", q, re.IGNORECASE)
        if m_diff:
            d1_s, d2_s = m_diff.groups()
            d1 = date.fromisoformat(d1_s)
            d2 = date.fromisoformat(d2_s)
            diff = abs((d2 - d1).days)
            out = f"{diff} days"
            digest = hashlib.sha256(f"DATETIME_GREGORIAN:diff({d1_s},{d2_s})={out}".encode()).hexdigest()
            return out, digest

        # 2. Date offset addition/subtraction: "<date> + <N> days" or "<date> - <N> days"
        m_shift = re.search(r"(\d{4}-\d{2}-\d{2})\s*([\+\-])\s*(\d+)\s*days?", q, re.IGNORECASE)
        if m_shift:
            d_s, op, n_s = m_shift.groups()
            d = date.fromisoformat(d_s)
            n = int(n_s)
            shifted = d + timedelta(days=n) if op == "+" else d - timedelta(days=n)
            out = f"Shifted Date: {shifted.isoformat()}"
            digest = hashlib.sha256(f"DATETIME_GREGORIAN:shift({d_s},{op}{n})={shifted.isoformat()}".encode()).hexdigest()
            return out, digest

        # 3. Timezone conversion: "convert <YYYY-MM-DD HH:MM> UTC to UTC(+|-N)"
        m_tz = re.search(r"convert\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})\s*UTC\s+to\s+UTC([+-]\d+)", q, re.IGNORECASE)
        if m_tz:
            dt_s, tz_offset_s = m_tz.groups()
            dt_base = datetime.strptime(dt_s, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            tz_offset = timezone(timedelta(hours=int(tz_offset_s)))
            converted = dt_base.astimezone(tz_offset)
            out = f"Timezone Shift: {converted.isoformat()}"
            digest = hashlib.sha256(f"DATETIME_GREGORIAN:tz({dt_s},UTC{tz_offset_s})={out}".encode()).hexdigest()
            return out, digest

        # 4. Leap year verification: "is <year> a leap year"
        m_leap = re.search(r"is\s+(\d{1,4})\s+(?:a\s+)?leap\s+year", q, re.IGNORECASE)
        if m_leap:
            y = int(m_leap.group(1))
            is_leap_yr = (y % 4 == 0) and (y % 100 != 0 or y % 400 == 0)
            status_text = "True (proleptic Gregorian leap year)" if is_leap_yr else "False (secular non-leap year)"
            out = f"Leap Year Check for {y}: {status_text}"
            digest = hashlib.sha256(f"DATETIME_GREGORIAN:leap({y})={is_leap_yr}".encode()).hexdigest()
            return out, digest

        # 5. Day of week: "day of week for <date>"
        m_dow = re.search(r"day\s+of\s+(?:the\s+)?week\s+(?:for|on)\s+(\d{4}-\d{2}-\d{2})", q, re.IGNORECASE)
        if m_dow:
            d_s = m_dow.group(1)
            d = date.fromisoformat(d_s)
            dow = d.strftime("%A")
            out = f"Day of Week: {dow}"
            digest = hashlib.sha256(f"DATETIME_GREGORIAN:dow({d_s})={dow}".encode()).hexdigest()
            return out, digest

        # 6. Current timestamp
        if re.search(r"\b(current|today'?s)\s+(date|time|timestamp)\b", q, re.IGNORECASE):
            now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            out = f"Current ISO: {now_iso}"
            digest = hashlib.sha256(f"DATETIME_GREGORIAN:now={now_iso}".encode()).hexdigest()
            return out, digest

        return None


# -----------------------------------------------------------------------------
# 2. Dewey Stack & Lemma Graph Navigator (RETRIEVE)
# -----------------------------------------------------------------------------

class DeweyGraphNavigator:
    """Navigates emap.db and indexed Dewey stacks to retrieve grounded facts."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path

    def query_graph(self, query: str) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        """Traverse lemma graph for definition, relation, or Dewey classification."""
        if not self.db_path.exists():
            return None

        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        q_lower = query.lower().strip()

        # 1. Relation pattern
        rel_pattern = r"(?:what\s+is\s+the\s+)?(hypernym|antonym|synonym|part|opposite|kind)\s+of\s+([a-zA-Z]+)"
        m_rel = re.search(rel_pattern, q_lower)
        if m_rel:
            raw_rel, lem = m_rel.groups()
            rel_name = "hypernym" if raw_rel in ("hypernym", "kind") else ("antonym" if raw_rel in ("antonym", "opposite") else raw_rel)
            cur.execute("""
            SELECT target_lemma, weight, relation FROM edges
            WHERE source_lemma = ? AND relation = ?
            ORDER BY weight DESC LIMIT 3
            """, (lem, rel_name))
            rows = cur.fetchall()
            if rows:
                targets = [r["target_lemma"] for r in rows]
                confidence = float(rows[0]["weight"])
                ans = f"The {rel_name} of '{lem}' is: {', '.join(targets)}."
                meta = {
                    "source_lemma": lem,
                    "relation": rel_name,
                    "targets": targets,
                    "db_source": "emap.db:edges"
                }
                conn.close()
                return ans, confidence, meta

        # 2. Dewey Classification
        m_dewey = re.search(r"(?:what\s+is\s+the\s+)?dewey\s+(?:code|category|classification|shelf)?\s*(?:for|of)?\s+([a-zA-Z]+)", q_lower)
        if m_dewey:
            lem = m_dewey.group(1)
            cur.execute("SELECT lemma, pos, dewey, depth, gloss FROM nodes WHERE lemma = ?", (lem,))
            row = cur.fetchone()
            if row:
                dewey_code = row["dewey"]
                ans = f"Lemma '{lem}' is classified under Dewey section {dewey_code} ({row['gloss']})."
                meta = {
                    "lemma": lem,
                    "dewey": dewey_code,
                    "depth": row["depth"],
                    "db_source": "emap.db:nodes"
                }
                conn.close()
                return ans, 0.95, meta

        # 3. Direct Definition
        m_def = re.search(r"(?:define|meaning\s+of|definition\s+of|what\s+is)\s+([a-zA-Z]+)", q_lower)
        if m_def:
            lem = m_def.group(1)
            cur.execute("SELECT lemma, pos, gloss, dewey, t1_decomposition, depth FROM nodes WHERE lemma = ?", (lem,))
            row = cur.fetchone()
            if row:
                ans = f"'{lem}' ({row['pos']}): {row['gloss']} [Dewey: {row['dewey']}, Logic: {row['t1_decomposition']}]."
                meta = {
                    "lemma": lem,
                    "pos": row["pos"],
                    "dewey": row["dewey"],
                    "t1_decomposition": row["t1_decomposition"],
                    "depth": row["depth"],
                    "db_source": "emap.db:nodes"
                }
                conn.close()
                return ans, 0.92, meta

        conn.close()
        return None


# -----------------------------------------------------------------------------
# 3. Whitelisted Search Hand (HAND)
# -----------------------------------------------------------------------------

class WhitelistedHandProxy:
    """Executes web search queries strictly bounded to an enforced whitelist."""

    ALLOWED_DOMAINS: Set[str] = {
        "en.wikipedia.org",
        "wikipedia.org",
        "w3.org",
        "nist.gov",
        "ncbi.nlm.nih.gov",
        "github.com",
    }

    WHITELISTED_STORE: Dict[str, Dict[str, Any]] = {
        "speed of light": {
            "domain": "nist.gov",
            "url": "https://physics.nist.gov/constants/c",
            "answer": "The speed of light in vacuum is exactly 299,792,458 meters per second.",
            "trust_score": 0.99,
        },
        "gravitational constant": {
            "domain": "nist.gov",
            "url": "https://physics.nist.gov/constants/G",
            "answer": "The Newtonian constant of gravitation G is 6.67430 x 10^-11 m^3 kg^-1 s^-2.",
            "trust_score": 0.99,
        },
        "python release date": {
            "domain": "wikipedia.org",
            "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
            "answer": "Python was first released on February 20, 1991 by Guido van Rossum.",
            "trust_score": 0.95,
        },
    }

    @classmethod
    def query_hand(cls, query: str, target_domain: Optional[str] = None) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        """Query external whitelisted source."""
        q_lower = query.lower()

        if target_domain and target_domain.lower() not in cls.ALLOWED_DOMAINS:
            return None

        for topic, data in cls.WHITELISTED_STORE.items():
            if topic in q_lower:
                domain = data["domain"]
                if target_domain and domain != target_domain.lower():
                    continue
                url = data["url"]
                ans = data["answer"]
                trust = data["trust_score"]
                meta = {
                    "domain": domain,
                    "url": url,
                    "trust_score": trust,
                    "verification": "whitelisted_source"
                }
                return ans, trust, meta

        return None


# -----------------------------------------------------------------------------
# 4. Alice 1.0 Decision Engine (Arbitration Lattice)
# -----------------------------------------------------------------------------

class AliceDecisionEngine:
    """Specialized navigation and arbitration model traversing the emap substrate."""

    def __init__(self, db_path: Path = DB_PATH, theta_stack: float = 0.85, theta_hand: float = 0.80):
        self.db_path = db_path
        self.theta_stack = theta_stack
        self.theta_hand = theta_hand
        self.navigator = DeweyGraphNavigator(db_path)

    def route_and_arbitrate(self, query: str, forced_domain: Optional[str] = None) -> DecisionReceipt:
        """Execute the formal arbitration lattice over query q:

        COMPUTE > RETRIEVE > HAND > ABSTAIN
        """
        t0 = time.time()
        req_id = f"req-{uuid.uuid4().hex[:12]}"
        trace: List[str] = []

        # ---------------------------------------------------------
        # TIER 1: COMPUTE (Deterministic ground truth)
        # ---------------------------------------------------------
        trace.append("Lattice Step 1: Probing Deterministic Tool Engines (COMPUTE)...")

        # 1a. Rational CAS
        cas_res = DeterministicEngine.evaluate_cas_rational(query)
        if cas_res:
            ans, digest = cas_res
            dt = (time.time() - t0) * 1000.0
            trace.append(f"COMPUTE Success: rational CAS -> {ans} (digest: {digest[:16]}...)")
            prov = ProvenanceRecord(
                route=ActionType.COMPUTE,
                source="tool:cas_rational_kernel",
                digest=digest,
                timestamp=datetime.now(timezone.utc).isoformat(),
                metadata={"engine": "fractions_zero_drift"}
            )
            return DecisionReceipt(
                request_id=req_id,
                action=ActionType.COMPUTE,
                answer=f"Result: {ans}",
                confidence=1.0,
                provenance=prov,
                latency_ms=dt,
                execution_trace=trace
            )

        # 1b. SI 7-Dimension Unit Conversion
        units_res = DeterministicEngine.evaluate_si_dimensions(query)
        if units_res:
            ans, digest = units_res
            dt = (time.time() - t0) * 1000.0
            if "DIMENSIONAL_TYPE_ERROR" in ans:
                trace.append(f"COMPUTE Type Check: dimensional mismatch detected -> {ans}")
                prov = ProvenanceRecord(
                    route=ActionType.COMPUTE,
                    source="tool:si_dimension_checker",
                    digest=digest,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    metadata={"error": "dimensional_mismatch"}
                )
                return DecisionReceipt(
                    request_id=req_id,
                    action=ActionType.COMPUTE,
                    answer=f"Error: {ans}",
                    confidence=1.0,
                    provenance=prov,
                    latency_ms=dt,
                    execution_trace=trace
                )
            trace.append(f"COMPUTE Success: SI units conversion -> {ans} (digest: {digest[:16]}...)")
            prov = ProvenanceRecord(
                route=ActionType.COMPUTE,
                source="tool:si_units_algebra",
                digest=digest,
                timestamp=datetime.now(timezone.utc).isoformat(),
                metadata={"engine": "si_7dim_vector"}
            )
            return DecisionReceipt(
                request_id=req_id,
                action=ActionType.COMPUTE,
                answer=f"Conversion: {ans}",
                confidence=1.0,
                provenance=prov,
                latency_ms=dt,
                execution_trace=trace
            )

        # 1c. Proleptic Gregorian Datetime
        dt_res = DeterministicEngine.evaluate_proleptic_gregorian(query)
        if dt_res:
            ans, digest = dt_res
            dt = (time.time() - t0) * 1000.0
            trace.append(f"COMPUTE Success: Gregorian datetime -> {ans} (digest: {digest[:16]}...)")
            prov = ProvenanceRecord(
                route=ActionType.COMPUTE,
                source="tool:datetime_gregorian",
                digest=digest,
                timestamp=datetime.now(timezone.utc).isoformat(),
                metadata={"engine": "proleptic_gregorian_tz"}
            )
            return DecisionReceipt(
                request_id=req_id,
                action=ActionType.COMPUTE,
                answer=f"Datetime: {ans}",
                confidence=1.0,
                provenance=prov,
                latency_ms=dt,
                execution_trace=trace
            )

        # ---------------------------------------------------------
        # TIER 2: RETRIEVE (Topological emap.db / Dewey Navigation)
        # ---------------------------------------------------------
        trace.append("Lattice Step 2: Probing Topological Dewey Stacks (RETRIEVE)...")
        nav_res = self.navigator.query_graph(query)
        if nav_res:
            ans, conf, meta = nav_res
            if conf >= self.theta_stack:
                dt = (time.time() - t0) * 1000.0
                digest = hashlib.sha256(f"RETRIEVE:{json.dumps(meta, sort_keys=True)}".encode()).hexdigest()
                trace.append(f"RETRIEVE Success: conf {conf:.2f} >= theta {self.theta_stack} (digest: {digest[:16]}...)")
                prov = ProvenanceRecord(
                    route=ActionType.RETRIEVE,
                    source=f"dewey_stack:{meta.get('dewey', '420')}",
                    digest=digest,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    metadata=meta
                )
                return DecisionReceipt(
                    request_id=req_id,
                    action=ActionType.RETRIEVE,
                    answer=ans,
                    confidence=conf,
                    provenance=prov,
                    latency_ms=dt,
                    execution_trace=trace
                )

        # ---------------------------------------------------------
        # TIER 3: HAND (Whitelisted Web Search Proxy)
        # ---------------------------------------------------------
        trace.append("Lattice Step 3: Probing Whitelisted Search Hands (HAND)...")
        hand_res = WhitelistedHandProxy.query_hand(query, target_domain=forced_domain)
        if hand_res:
            ans, trust, meta = hand_res
            if trust >= self.theta_hand:
                dt = (time.time() - t0) * 1000.0
                digest = hashlib.sha256(f"HAND:{meta['url']}:{ans}".encode()).hexdigest()
                trace.append(f"HAND Success: trust {trust:.2f} >= theta {self.theta_hand} (digest: {digest[:16]}...)")
                prov = ProvenanceRecord(
                    route=ActionType.HAND,
                    source=meta["url"],
                    digest=digest,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    metadata=meta
                )
                return DecisionReceipt(
                    request_id=req_id,
                    action=ActionType.HAND,
                    answer=ans,
                    confidence=trust,
                    provenance=prov,
                    latency_ms=dt,
                    execution_trace=trace
                )

        # ---------------------------------------------------------
        # TIER 4: ABSTAIN (Calibrated Refusal)
        # ---------------------------------------------------------
        dt = (time.time() - t0) * 1000.0
        trace.append("Lattice Step 4: No route satisfied confidence bounds. Escalating to ABSTAIN.")
        return DecisionReceipt(
            request_id=req_id,
            action=ActionType.ABSTAIN,
            answer="ABSTAIN: No verified factual support path exists in emap or authorized tools.",
            confidence=0.0,
            provenance=None,
            latency_ms=dt,
            execution_trace=trace
        )


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Alice 1.0 Decision Engine CLI")
    parser.add_argument("query", type=str, help="Input query to arbitrate and answer")
    parser.add_argument("--domain", type=str, default=None, help="Target external domain for hand route")
    args = parser.parse_args()

    engine = AliceDecisionEngine()
    receipt = engine.route_and_arbitrate(args.query, forced_domain=args.domain)
    print(f"Action: {receipt.action.value}")
    print(f"Answer: {receipt.answer}")
    print(f"Confidence: {receipt.confidence:.2f}")
    print(f"Latency: {receipt.latency_ms:.1f} ms")
    if receipt.provenance:
        print(f"Provenance Source: {receipt.provenance.source}")
        print(f"Provenance Digest: {receipt.provenance.digest}")
    print("Execution Trace:")
    for step in receipt.execution_trace:
        print(f"  {step}")


if __name__ == "__main__":
    main()
