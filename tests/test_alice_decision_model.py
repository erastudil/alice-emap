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
import unittest

try:
    import pytest
except ImportError:
    import contextlib

    class _PytestFallback:
        @staticmethod
        def fixture(*args, **kwargs):
            def _decorator(fn):
                return fn
            return _decorator

        @staticmethod
        @contextlib.contextmanager
        def raises(exc_type):
            try:
                yield
            except exc_type:
                return
            raise AssertionError(f"Expected {exc_type.__name__} to be raised")

    pytest = _PytestFallback()

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

    def test_speech_canon_act_stamping(self, engine: AliceDecisionEngine):
        """Test SPEECH_CANON.md act stamping across COMPUTE, dimensional error, RETRIEVE, HAND, and ABSTAIN."""
        r_compute = engine.route_and_arbitrate("simplify 3/4 + 1/6")
        assert r_compute.act == "say"

        r_dim_err = engine.route_and_arbitrate("convert 10 km to kg")
        assert r_dim_err.act == "silence-instrument"

        r_retrieve = engine.route_and_arbitrate("define people")
        assert r_retrieve.act == "cite"

        r_hand = engine.route_and_arbitrate("what is the speed of light from nist.gov")
        assert r_hand.act == "cite"

        r_abstain = engine.route_and_arbitrate("who was the purple emperor of the moon in year 1234")
        assert r_abstain.act == "silence-gap"


    def test_l1_frame_table_coverage(self, engine: AliceDecisionEngine):
        """Test all 14 L1 frames in alice_frames.py match canonical prompts (Q3.1)."""
        from alice_frames import FRAME_TABLE, match_l1_frame

        assert len(FRAME_TABLE) == 14
        samples = {
            "define": "define people",
            "dewey": "what is the dewey classification of body",
            "hypernym": "what is a kind of people",
            "hyponym": "examples of being",
            "part": "parts of face",
            "antonym": "opposite of other",
            "synonym": "synonym of someone",
            "cause": "what does become cause",
            "convert": "convert 100 km to miles",
            "arithmetic": "calculate 2^10",
            "datetime": "2026-10-05 + 45 days",
            "feature": "how do I use the stacks",
            "fresh": "what is the speed of light from nist.gov",
            "stack": "tell me about speed of light",
        }
        for expected_frame, prompt in samples.items():
            matched = match_l1_frame(prompt)
            assert matched is not None, f"Failed to match frame for {prompt}"
            assert matched.frame == expected_frame

    def test_retrieve_relational_frames_and_compare(self, engine: AliceDecisionEngine):
        """Test hyponym, part, antonym, synonym, and cause frames over emap.db (Q3.3, Q3.4)."""
        r_hypo = engine.route_and_arbitrate("examples of being")
        assert r_hypo.action == ActionType.RETRIEVE
        assert "organism" in r_hypo.answer
        assert r_hypo.provenance.metadata["frame"] == "hyponym"
        assert r_hypo.act == "cite"

        r_part = engine.route_and_arbitrate("parts of face")
        assert r_part.action == ActionType.RETRIEVE
        assert "eye" in r_part.answer
        assert r_part.provenance.metadata["frame"] == "part"

        r_ant = engine.route_and_arbitrate("opposite of other")
        assert r_ant.action == ActionType.RETRIEVE
        assert "same" in r_ant.answer
        assert r_ant.provenance.metadata["frame"] == "antonym"

        r_syn = engine.route_and_arbitrate("synonym of someone")
        assert r_syn.action == ActionType.RETRIEVE
        assert "somebody" in r_syn.answer
        assert r_syn.provenance.metadata["frame"] == "synonym"

        r_cause = engine.route_and_arbitrate("what does become cause")
        assert r_cause.action == ActionType.RETRIEVE
        assert "be" in r_cause.answer
        assert r_cause.provenance.metadata["frame"] == "cause"

    def test_pointer_walk_records_hops(self, engine: AliceDecisionEngine):
        """Test open pointer edges (form_of, pertainym, derivation) resolve and record hops (Q3.2)."""
        r_form = engine.route_and_arbitrate("define was")
        assert r_form.action == ActionType.RETRIEVE
        assert any("form_of-->be" in h for h in r_form.provenance.metadata["hops"])

        r_pert = engine.route_and_arbitrate("define your")
        assert r_pert.action == ActionType.RETRIEVE
        assert any("pertainym-->you" in h for h in r_pert.provenance.metadata["hops"])

        r_deriv = engine.route_and_arbitrate("define softness")
        assert r_deriv.action == ActionType.RETRIEVE
        assert any("soft--derivation-->softness" in h for h in r_deriv.provenance.metadata["hops"])

    def test_compose_scalar_card_plus_convert(self, engine: AliceDecisionEngine):
        """Test Q7.1 COMPOSE rule: scalar card + unit conversion with two receipt steps."""
        receipt = engine.route_and_arbitrate("speed of light in miles per hour")
        assert receipt.action == ActionType.COMPOSE
        assert receipt.act == "cite"
        assert "670616629" in receipt.answer
        assert len(receipt.provenance.metadata["steps"]) == 2
        assert len(receipt.provenance.digest) == 64

    def test_compose_date_card_plus_day_offset(self, engine: AliceDecisionEngine):
        """Test Q7.2 COMPOSE rule: date card + day offset with calendar tool digest on second step."""
        receipt = engine.route_and_arbitrate("python release date + 100 days")
        assert receipt.action == ActionType.COMPOSE
        assert receipt.act == "cite"
        assert "1991-05-31" in receipt.answer
        assert receipt.provenance.source == "tool:datetime_gregorian"
        assert len(receipt.provenance.metadata["steps"]) == 2
        assert len(receipt.provenance.digest) == 64

    def test_speech_canon_act_stamps(self, engine: AliceDecisionEngine):
        """Test Q3.5: every receipt carries a valid act from SPEECH_CANON.md."""
        from alice_decision_engine import SPEECH_CANON

        r_say = engine.route_and_arbitrate("simplify 3/4 + 1/6")
        assert r_say.act == "say" and r_say.act in SPEECH_CANON

        r_cite = engine.route_and_arbitrate("define people")
        assert r_cite.act == "cite" and r_cite.act in SPEECH_CANON

        r_gap = engine.route_and_arbitrate("who was the purple emperor of the moon in year 1234")
        assert r_gap.act == "silence-gap" and r_gap.act in SPEECH_CANON


class TestAliceDecisionModelUnittest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = AliceDecisionEngine()
        cls.suite = TestAliceDecisionModel()

    def test_decision_engine_suite(self):
        for name in sorted(dir(self.suite)):
            if name.startswith("test_"):
                with self.subTest(check=name):
                    getattr(self.suite, name)(self.engine)


if __name__ == "__main__":
    unittest.main()
