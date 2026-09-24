"""Tests for the TRIZBench comparison tool (no real dataset needed)."""
import importlib.util
import json
from pathlib import Path

import pytest

EVAL = Path(__file__).resolve().parent / "eval"
spec = importlib.util.spec_from_file_location("tb", EVAL / "trizbench_eval.py")
tb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tb)


def rec(pid, plus, minus, text="ABSTRACT: something useful"):
    return {"patent_id": pid, "input_text": text,
            "gold_json": str({"plus_ids": plus, "minus_ids": minus})}


def test_load_records_keeps_only_single_pair_with_text(tmp_path):
    p = tmp_path / "t.jsonl"
    rows = [rec("A", [10], [5]), rec("B", [], []), rec("C", [1, 2], [3]),
            rec("D", [7], [8], text=""), rec("E", [40], [3]), rec("F", [4], [4])]
    p.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    kept = tb.load_records(p)
    assert [r["patent_id"] for r in kept] == ["A"]
    assert kept[0]["gold"] == (10, 5)


def test_sample_is_reproducible_and_bounded():
    recs = [{"patent_id": str(i), "gold": (1, 2), "text": "x"} for i in range(50)]
    a = tb.sample(recs, 10, seed=1)
    assert a == tb.sample(recs, 10, seed=1)
    assert len(a) == 10 and a != tb.sample(recs, 10, seed=2)
    assert len(tb.sample(recs, 999, seed=1)) == 50


def test_to_cases_truncates_and_labels_english():
    recs = [{"patent_id": "US1", "gold": (1, 2), "text": "a" * 5000}]
    case = tb.to_cases(recs, max_chars=100)[0]
    assert case["id"] == "US1" and case["lang"] == "en" and len(case["problem"]) == 100


def test_rank_pairs_orders_by_rank_sum_and_skips_identical():
    pairs = tb.rank_pairs([1, 2], [3, 1])
    assert pairs[0] == (1, 3)
    assert (1, 1) not in pairs
    assert set(pairs) == {(1, 3), (2, 3), (2, 1)}


def test_metrics_exact_and_family():
    m = tb.metrics((10, 5), improve=[10, 4], worsen=[6, 5])
    assert m["improve_hit"] and m["worsen_hit"] and m["pair_lenient"]
    assert m["hit3"] is True          # (10,6) then (10,5) are within the first three ranked pairs
    assert m["top1"] is False
    fam = tb.metrics((3, 5), improve=[4], worsen=[6])   # 4~3 and 6~5 are moving/stationary twins
    assert fam["hit3"] is False and fam["hit3_family"] is True


def test_metrics_miss_and_empty():
    m = tb.metrics((10, 5), improve=[1, 2, 3], worsen=[7, 8, 9])
    assert not any([m["improve_hit"], m["worsen_hit"], m["pair_lenient"], m["hit3"], m["top1"]])
    e = tb.metrics((10, 5), improve=[], worsen=[])
    assert e["hit3"] is False


def test_summarize_rates():
    rows = [tb.metrics((1, 2), [1], [2]), tb.metrics((1, 2), [3], [4])]
    s = tb.summarize(rows)
    assert s["n"] == 2 and s["hit3"] == 0.5 and s["top1"] == 0.5


def test_pending_cases_skips_valid_results_and_retries_failures():
    cases = [{"id": "A"}, {"id": "B"}, {"id": "C"}, {"id": "D"}]
    existing = {
        "A": {"plugin_loaded": True, "exit_code": 0, "improve": [1], "worsen": [2]},
        "B": {"plugin_loaded": True, "exit_code": 1, "improve": [], "worsen": []},   # usage limit
        "C": {"plugin_loaded": True, "exit_code": 0, "improve": [1], "worsen": []},  # unparsed
    }
    assert [c["id"] for c in tb.pending_cases(cases, existing)] == ["B", "C", "D"]
    assert tb.pending_cases(cases, {}) == cases


def test_to_cases_deduplicates_repeated_patent_ids():
    recs = [{"patent_id": "US1", "gold": (1, 2), "text": "x"}, {"patent_id": "US1", "gold": (3, 4), "text": "x"}]
    assert len(tb.to_cases(recs)) == 1
