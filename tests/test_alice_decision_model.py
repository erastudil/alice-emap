"""test_alice_decision_model.py - Expanded Test Suite for Alice 1.0 Decision Engine.

Verifies:
1. Rational CAS exact arithmetic evaluation (fractions, powers, gcd, lcm).
2. Proleptic Gregorian datetime engine (differences, shifts, timezone conversions, leap years).
3. SI 7-dimension dimensional unit algebra (consistency verification and mismatch rejection).
4. RETRIEVE topological navigation over emap.db and Dewey stacks.
5. HAND query routing against enforced domain whitelist.
6. ABSTAIN calibrated refusal on unprovenanced questions.
7. Cryptographic provenance digest presence (64-char SHA256 hex) on all emissions.
"""

import re
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from alice_decision_engine import ActionType, AliceDecisionEngine, DecisionReceipt


@pytest.fixture(scope="module")
def engine():
    """Instantiate Alice Decision Engine with canonical emap database."""
    return AliceDecisionEngine()


class TestAliceDecisionModel:

    # -------------------------------------------------------------------------
    # 1. Rational CAS Exact Evaluation
    # -------------------------------------------------------------------------

    def test_cas_rational_fraction_addition(self, engine: AliceDecisionEngine):
        """Test exact rational addition without floating point drift: 3/4 + 1/6 = 11/12."""
        receipt = engine.route_and_arbitrate("simplify 3/4 + 1/6")
        assert receipt.action == ActionType.COMPUTE
        assert receipt.confidence == 1.0
        assert "11/12" in receipt.answer
        assert receipt.provenance is not None
        assert receipt.provenance.source == "tool:cas_rational_kernel"
        assert len(receipt.provenance.digest) == 64

    def test_cas_rational_power_evaluation(self, engine: AliceDecisionEngine):
        """Test exact power evaluation: 2^10 = 1024."""
        receipt = engine.route_and_arbitrate("calculate 2^10")
        assert receipt.action == ActionType.COMPUTE
        assert "1024" in receipt.answer
        assert receipt.provenance is not None

    def test_cas_rational_algebraic_reduction(self, engine: AliceDecisionEngine):
        """Test algebraic fraction multiplication reduction: (2/5) * (15/4) = 3/2."""
        receipt = engine.route_and_arbitrate("calculate (2/5) * (15/4)")
        assert receipt.action == ActionType.COMPUTE
        assert "3/2" in receipt.answer

    def test_cas_gcd_lcm(self, engine: AliceDecisionEngine):
        """Test exact GCD and LCM calculation."""
        receipt_gcd = engine.route_and_arbitrate("gcd(84, 36)")
        assert receipt_gcd.action == ActionType.COMPUTE
        assert "12" in receipt_gcd.answer

        receipt_lcm = engine.route_and_arbitrate("lcm(12, 18)")
        assert receipt_lcm.action == ActionType.COMPUTE
        assert "36" in receipt_lcm.answer

    # -------------------------------------------------------------------------
    # 2. Proleptic Gregorian Datetime Calculations
    # -------------------------------------------------------------------------

    def test_datetime_day_difference(self, engine: AliceDecisionEngine):
        """Test exact elapsed days between dates."""
        receipt = engine.route_and_arbitrate("days between 2026-01-01 and 2026-10-05")
        assert receipt.action == ActionType.COMPUTE
        assert "277 days" in receipt.answer
        assert receipt.provenance.source == "tool:datetime_gregorian"

    def test_datetime_offset_shift(self, engine: AliceDecisionEngine):
        """Test date shift addition and subtraction."""
        receipt_add = engine.route_and_arbitrate("2026-10-05 + 45 days")
        assert receipt_add.action == ActionType.COMPUTE
        assert "2026-11-19" in receipt_add.answer

        receipt_sub = engine.route_and_arbitrate("2026-10-05 - 100 days")
        assert receipt_sub.action == ActionType.COMPUTE
        assert "2026-06-27" in receipt_sub.answer

    def test_datetime_timezone_conversion(self, engine: AliceDecisionEngine):
        """Test timezone offset conversion."""
        receipt = engine.route_and_arbitrate("convert 2026-10-05 14:00 UTC to UTC-5")
        assert receipt.action == ActionType.COMPUTE
        assert "2026-10-05T09:00:00-05:00" in receipt.answer

    def test_datetime_leap_year(self, engine: AliceDecisionEngine):
        """Test proleptic Gregorian leap year rules."""
        receipt_2024 = engine.route_and_arbitrate("is 2024 a leap year")
        assert receipt_2024.action == ActionType.COMPUTE
        assert "True" in receipt_2024.answer

        receipt_1900 = engine.route_and_arbitrate("is 1900 a leap year")
        assert receipt_1900.action == ActionType.COMPUTE
        assert "False" in receipt_1900.answer

    # -------------------------------------------------------------------------
    # 3. SI 7-Dimension Unit Conversion
    # -------------------------------------------------------------------------

    def test_si_units_length_conversion(self, engine: AliceDecisionEngine):
        """Test valid length conversion with SI dimension [1,0,0,0,0,0,0]."""
        receipt = engine.route_and_arbitrate("convert 100 km to miles")
        assert receipt.action == ActionType.COMPUTE
        assert "Dimension: [1,0,0,0,0,0,0]" in receipt.answer
        assert "62.1371" in receipt.answer

    def test_si_units_speed_conversion(self, engine: AliceDecisionEngine):
        """Test valid velocity conversion with SI dimension [1,0,-1,0,0,0,0]."""
        receipt = engine.route_and_arbitrate("convert 60 mph to km/h")
        assert receipt.action == ActionType.COMPUTE
        assert "Dimension: [1,0,-1,0,0,0,0]" in receipt.answer
        assert "96.5606" in receipt.answer

    def test_si_units_temperature_affine(self, engine: AliceDecisionEngine):
        """Test temperature conversion with affine offset."""
        receipt = engine.route_and_arbitrate("convert 100 C to F")
        assert receipt.action == ActionType.COMPUTE
        assert "212.00 F" in receipt.answer
        assert "Dimension: [0,0,0,0,1,0,0]" in receipt.answer

    def test_si_units_dimensional_mismatch_rejection(self, engine: AliceDecisionEngine):
        """Test dimensional type error on incompatible units (length vs mass)."""
        receipt = engine.route_and_arbitrate("convert 10 km to kg")
        assert receipt.action == ActionType.COMPUTE
        assert "DIMENSIONAL_TYPE_ERROR" in receipt.answer
        assert receipt.provenance.source == "tool:si_dimension_checker"

    # -------------------------------------------------------------------------
    # 4. Topological Navigation, Hand Routing, and Abstention
    # -------------------------------------------------------------------------

    def test_retrieve_navigation_definition(self, engine: AliceDecisionEngine):
        """Test concept definition retrieval from emap graph."""
        receipt = engine.route_and_arbitrate("define people")
        assert receipt.action == ActionType.RETRIEVE
        assert receipt.confidence >= 0.85
        assert "people" in receipt.answer.lower()
        assert "dewey_stack" in receipt.provenance.source

    def test_retrieve_navigation_dewey_shelf(self, engine: AliceDecisionEngine):
        """Test Dewey classification coordinate query on emap nodes."""
        receipt = engine.route_and_arbitrate("what is the dewey classification of body")
        assert receipt.action == ActionType.RETRIEVE
        assert receipt.confidence >= 0.85

    def test_hand_whitelisted_routing(self, engine: AliceDecisionEngine):
        """Test whitelisted query routes to HAND with trust score and source URL."""
        receipt = engine.route_and_arbitrate("what is the speed of light from nist.gov")
        assert receipt.action == ActionType.HAND
        assert receipt.confidence >= 0.80
        assert "299,792,458" in receipt.answer
        assert "nist.gov" in receipt.provenance.source

    def test_hand_unauthorized_domain_rejection(self, engine: AliceDecisionEngine):
        """Test unwhitelisted domain is rejected and falls back to ABSTAIN."""
        receipt = engine.route_and_arbitrate("what is the speed of light", forced_domain="malicious-untrusted.com")
        assert receipt.action != ActionType.HAND

    def test_abstain_unprovenanced_query(self, engine: AliceDecisionEngine):
        """Test ungrounded, absurd counterfactual triggers calibrated ABSTAIN."""
        receipt = engine.route_and_arbitrate("who was the purple emperor of the moon in year 1234")
        assert receipt.action == ActionType.ABSTAIN
        assert receipt.confidence == 0.0
        assert "ABSTAIN" in receipt.answer
        assert receipt.provenance is None

    def test_provenance_digest_structure(self, engine: AliceDecisionEngine):
        """Test all non-abstain actions emit 64-char hex SHA256 provenance digests."""
        queries = [
            "simplify 3/4 + 1/6",
            "convert 100 km to miles",
            "days between 2026-01-01 and 2026-10-05",
            "define kind",
            "what is the speed of light"
        ]
        for q in queries:
            receipt = engine.route_and_arbitrate(q)
            if receipt.action != ActionType.ABSTAIN:
                assert receipt.provenance is not None
                assert isinstance(receipt.provenance.digest, str)
                assert len(receipt.provenance.digest) == 64
                assert re.match(r"^[0-9a-f]{64}$", receipt.provenance.digest) is not None
                assert receipt.latency_ms > 0.0
