"""Session tests: stack cite, local hands, memory, personalities, and an honest miss."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from alice_session import run_turn


@pytest.fixture()
def memory_path(tmp_path: Path) -> Path:
    return tmp_path / "memory.db"


def test_compute_still_wins(memory_path: Path):
    turn = run_turn("simplify 3/4 + 1/6", memory_path=memory_path)
    assert turn["act"] == "say"
    assert turn["route"] == "COMPUTE"
    assert "11/12" in turn["answer"]
    assert len(turn["provenance"]["digest"]) == 64


def test_stack_card_cites_the_constant():
    turn = run_turn("what is the speed of light in vacuum", personality="researcher")
    assert turn["act"] == "cite"
    assert turn["route"] == "RETRIEVE"
    assert turn["source"].startswith("stack:")
    assert "299792458" in turn["answer"]
    assert "physics.nist.gov" in turn["answer"]
    assert turn["personality"] == "researcher"


def test_feature_how_to():
    turn = run_turn("how do I use the stacks", personality="coder")
    assert turn["act"] == "cite"
    assert turn["source"] == "feature:stacks"
    assert "Dewey" in turn["answer"]


def test_memory_round_trip(memory_path: Path):
    kept = run_turn("remember preference: use pytest", personality="coder", memory_path=memory_path)
    assert kept["act"] == "say"
    assert "use pytest" in kept["answer"]
    recalled = run_turn("what do you remember about pytest", memory_path=memory_path)
    assert "use pytest" in recalled["answer"]
    forgotten = run_turn("forget: pytest", memory_path=memory_path)
    assert "Forgot 1 note" in forgotten["answer"]


def test_outside_domain_names_the_gap():
    turn = run_turn("who won the 1998 world series")
    assert turn["act"] == "silence-gap"
    assert turn["route"] == "ABSTAIN"
    assert turn["next"]
    assert turn["provenance"] is None


def test_unknown_personality():
    with pytest.raises(KeyError):
        run_turn("hello", personality="wizard")
