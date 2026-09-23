"""Tests for the eval cases and the scoring tool (DESIGN 10.1)."""
import importlib.util
import json
from pathlib import Path

import pytest

EVAL = Path(__file__).resolve().parent / "eval"
spec = importlib.util.spec_from_file_location("eval_score", EVAL / "score.py")
score_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(score_mod)

CASES = json.loads((EVAL / "cases.yaml").read_text(encoding="utf-8"))["cases"]


def test_twenty_cases_with_unique_ids():
    assert len(CASES) == 20
    assert len({c["id"] for c in CASES}) == 20


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_case_is_well_formed(case):
    assert case["problem"].strip()
    assert case["lang"] in ("ko", "en")
    for key in ("expected_improve", "expected_worsen"):
        assert case[key] and all(1 <= x <= 39 for x in case[key])
    assert not set(case["expected_improve"]) & set(case["expected_worsen"])


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_expected_pair_returns_principles(case):
    """Every case must be answerable from verified matrix data."""
    ranking = score_mod.real_matrix(case["expected_improve"], case["expected_worsen"])
    assert ranking, f"{case['id']}: expected pair gives no principles"


def fake_matrix(imp, wor):
    return {1, 2, 3}


CASES_2 = [
    {"id": "A", "expected_improve": [14], "expected_worsen": [1]},
    {"id": "B", "expected_improve": [9], "expected_worsen": [27]},
]


def test_score_hit_needs_both_sides_in_top3():
    results = {
        "A": {"improve": [5, 6, 14, 7], "worsen": [1], "principles_cited": [1]},   # 14 is 3rd: hit
        "B": {"improve": [9], "worsen": [4, 5, 6, 27], "principles_cited": []},    # 27 is 4th: miss
    }
    out = score_mod.score(CASES_2, results, matrix=fake_matrix)
    assert out["top3_hit_rate"] == 0.5
    assert out["improve_hit_rate"] == 1.0
    assert out["worsen_hit_rate"] == 0.5
    assert [r["hit"] for r in out["rows"]] == [True, False]


def test_score_counts_hallucinated_principles():
    results = {
        "A": {"improve": [14], "worsen": [1], "principles_cited": [1, 2, 39, 40]},
        "B": {"improve": [9], "worsen": [27], "principles_cited": [3]},
    }
    out = score_mod.score(CASES_2, results, matrix=fake_matrix)
    assert out["hallucinated_principles"] == 2
    assert out["rows"][0]["hallucinated_principles"] == [39, 40]


def test_score_lookup_error_counts_all_cited_as_hallucinated():
    results = {"A": {"improve": [14], "worsen": [14], "principles_cited": [1, 2]}}
    out = score_mod.score(CASES_2[:1], results, matrix=lambda i, w: None)
    assert out["hallucinated_principles"] == 2


def test_score_reports_missing_cases():
    out = score_mod.score(CASES_2, {"A": {"improve": [14], "worsen": [1]}}, matrix=fake_matrix)
    assert out["cases_missing"] == ["B"]
    assert out["cases_scored"] == 1
