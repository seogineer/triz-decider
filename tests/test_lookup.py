"""Tests for skills/triz-analysis/scripts/lookup.py (DESIGN.md 6장).

Logic tests run against a synthetic fixture: the script is copied next to a
tiny data dir, which also proves data paths resolve relative to the script.
Smoke tests run against the real data files and compare with the JSON itself.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "triz-analysis"
REAL_SCRIPT = SKILL / "scripts" / "lookup.py"
REAL_DATA = SKILL / "data"


def run(script, *args):
    p = subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True, text=True, encoding="utf-8",
    )
    out = json.loads(p.stdout) if p.stdout.strip() else None
    err = json.loads(p.stderr) if p.stderr.strip() else None
    return p.returncode, out, err


def write(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")


def default_cells():
    """Named cells used by the tests, plus one filler cell per row (except the
    declared-missing row 16) so that every other row counts as populated."""
    filler = {f"{r}-39" if r != 39 else "39-38": [40] for r in range(1, 40) if r != 16}
    named = {"1-2": [5, 3, 7], "1-3": [3, 9], "4-2": [9, 5],
             "9-2": [2, 28], "17-1": [1]}
    return {**filler, **named}


def make_env(tmp_path, cells=None, missing_rows=None, unverified=None):
    """Copy the script into tmp_path/scripts and create tmp_path/data."""
    (tmp_path / "scripts").mkdir()
    (tmp_path / "data").mkdir()
    script = tmp_path / "scripts" / "lookup.py"
    shutil.copy(REAL_SCRIPT, script)
    write(tmp_path / "data" / "parameters.json", {
        "version": "t", "source": "t",
        "parameters": [
            {"id": i, "name": {"en": f"Param{i}", "ko": f"파라미터{i}"},
             "definition": {"en": f"def{i}", "ko": f"정의{i}"},
             "keywords": ["속도", "speed"] if i == 9 else [f"kw{i}"]}
            for i in range(1, 40)
        ],
    })
    write(tmp_path / "data" / "contradiction-matrix.json", {
        "version": "t", "source": "t", "size": 39,
        "missing_rows": [16] if missing_rows is None else missing_rows,
        "unverified_cells": [] if unverified is None else unverified,
        "cells": cells if cells is not None else default_cells(),
    })
    write(tmp_path / "data" / "inventive-principles.json", {
        "version": "t", "source": "t",
        "principles": [
            {"id": i, "name": {"en": f"Prin{i}", "ko": f"원리{i}"},
             "sub_principles": {"ko": [f"하위{i}a", f"하위{i}b"], "en": [f"sub{i}a"]},
             "examples": {"ko": [f"예{i}"], "en": [f"ex{i}"]}}
            for i in range(1, 41)
        ],
    })
    write(tmp_path / "data" / "separation-principles.json", {
        "version": "t", "source": "t",
        "separations": [
            {"id": k, "name": {"en": k, "ko": k}, "related_principles": [1, 2]}
            for k in ("time", "space", "system", "condition")
        ],
    })
    return script


@pytest.fixture
def env(tmp_path):
    return make_env(tmp_path)


# ---------------------------------------------------------------- matrix ---

def test_matrix_pairs_in_input_order(env):
    code, out, err = run(env, "matrix", "--improve", "1,4", "--worsen", "2,3")
    assert code == 0 and err is None
    assert out["pairs"] == [
        {"improve": 1, "worsen": 2, "principles": [5, 3, 7]},
        {"improve": 1, "worsen": 3, "principles": [3, 9]},
        {"improve": 4, "worsen": 2, "principles": [9, 5]},
    ]


def test_matrix_empty_pairs_not_an_error(env):
    code, out, _ = run(env, "matrix", "--improve", "4", "--worsen", "3")
    assert code == 0
    assert out["pairs"] == []
    assert out["empty_pairs"] == [{"improve": 4, "worsen": 3}]
    assert out["ranking"] == []


def test_matrix_ranking_count_desc_ties_by_first_appearance(env):
    _, out, _ = run(env, "matrix", "--improve", "1,4", "--worsen", "2,3")
    # counts: 5->2, 3->2, 9->2, 7->1. First appearance order: 5, 3, 7, 9.
    assert [(r["id"], r["count"]) for r in out["ranking"]] == [
        (5, 2), (3, 2), (9, 2), (7, 1),
    ]


def test_matrix_ranking_name_follows_lang(env):
    _, ko, _ = run(env, "matrix", "--improve", "9", "--worsen", "2")
    _, en, _ = run(env, "matrix", "--improve", "9", "--worsen", "2", "--lang", "en")
    assert ko["ranking"][0]["name"] == "원리2"
    assert en["ranking"][0]["name"] == "Prin2"


def test_matrix_duplicate_ids_are_deduplicated(env):
    _, out, _ = run(env, "matrix", "--improve", "9,9", "--worsen", "2,2")
    assert len(out["pairs"]) == 1
    assert out["ranking"][0]["count"] == 1


def test_matrix_missing_row_reported_not_silent(env):
    code, out, _ = run(env, "matrix", "--improve", "16", "--worsen", "1")
    assert code == 0
    assert out["empty_pairs"] == [{"improve": 16, "worsen": 1}]
    assert out["warnings"] == [{"code": "missing_row", "improve": 16}]


def test_matrix_no_warnings_for_normal_pairs(env):
    _, out, _ = run(env, "matrix", "--improve", "1", "--worsen", "2")
    assert out["warnings"] == []


def test_matrix_direction_matters(env):
    _, out, _ = run(env, "matrix", "--improve", "17", "--worsen", "1")
    assert out["pairs"] == [{"improve": 17, "worsen": 1, "principles": [1]}]
    _, out, _ = run(env, "matrix", "--improve", "1", "--worsen", "17")
    assert out["pairs"] == []


# ---------------------------------------------------------- error codes ---

@pytest.mark.parametrize("args", [
    ["matrix"],
    ["matrix", "--improve", "1"],
    ["matrix", "--improve", "a", "--worsen", "2"],
    ["matrix", "--improve", "1,,2", "--worsen", "3"],
    ["matrix", "--improve", "", "--worsen", "3"],
    ["matrix", "--improve", "1.5", "--worsen", "3"],
    ["principle"],
    ["principle", "--id", "x"],
    ["param"],
    ["param", "--id", "1", "--search", "a"],
    ["param", "--search", ""],
    ["matrix", "--improve", "1", "--worsen", "2", "--lang", "fr"],
    ["nonexistent"],
    [],
])
def test_invalid_argument_exit_2(env, args):
    code, out, err = run(env, *args)
    assert code == 2
    assert out is None
    assert err["error"]["code"] == "invalid_argument"
    assert err["error"]["message"]


@pytest.mark.parametrize("args", [
    ["matrix", "--improve", "0", "--worsen", "2"],
    ["matrix", "--improve", "1", "--worsen", "40"],
    ["matrix", "--improve", "-1", "--worsen", "2"],
    ["principle", "--id", "41"],
    ["principle", "--id", "0"],
    ["param", "--id", "40"],
])
def test_out_of_range_exit_3(env, args):
    code, out, err = run(env, *args)
    assert code == 3
    assert out is None
    assert err["error"]["code"] == "out_of_range"


def test_same_parameter_exit_4(env):
    code, out, err = run(env, "matrix", "--improve", "9", "--worsen", "9")
    assert code == 4
    assert out is None
    assert err["error"]["code"] == "same_parameter"


def test_same_parameter_anywhere_in_lists_exit_4(env):
    code, _, err = run(env, "matrix", "--improve", "1,9", "--worsen", "2,9")
    assert code == 4
    assert err["error"]["code"] == "same_parameter"


def test_out_of_range_takes_precedence_over_same_parameter(env):
    code, _, err = run(env, "matrix", "--improve", "50", "--worsen", "50")
    assert code == 3


@pytest.mark.parametrize("victim", [
    "parameters.json", "contradiction-matrix.json", "inventive-principles.json",
])
def test_missing_data_file_exit_5(tmp_path, victim):
    script = make_env(tmp_path)
    (tmp_path / "data" / victim).unlink()
    args = {
        "parameters.json": ["param", "--id", "1"],
        "contradiction-matrix.json": ["matrix", "--improve", "1", "--worsen", "2"],
        "inventive-principles.json": ["principle", "--id", "1"],
    }[victim]
    code, out, err = run(script, *args)
    assert code == 5
    assert out is None
    assert err["error"]["code"] == "data_error"


def test_corrupt_data_file_exit_5(tmp_path):
    script = make_env(tmp_path)
    (tmp_path / "data" / "contradiction-matrix.json").write_text("{not json", encoding="utf-8")
    code, _, err = run(script, "matrix", "--improve", "1", "--worsen", "2")
    assert code == 5
    assert err["error"]["code"] == "data_error"


def test_matrix_with_unrelated_data_missing_still_works(tmp_path):
    """matrix needs the matrix + principle names; parameters.json is not required."""
    script = make_env(tmp_path)
    (tmp_path / "data" / "parameters.json").unlink()
    code, _, _ = run(script, "matrix", "--improve", "1", "--worsen", "2")
    assert code == 0


# ------------------------------------------------------------- principle ---

def test_principle_lookup_ko(env):
    code, out, _ = run(env, "principle", "--id", "1,15,35")
    assert code == 0
    assert [p["id"] for p in out["principles"]] == [1, 15, 35]
    p = out["principles"][0]
    assert p["name"] == "원리1"
    assert p["sub_principles"] == ["하위1a", "하위1b"]
    assert p["examples"] == ["예1"]


def test_principle_lookup_en(env):
    _, out, _ = run(env, "principle", "--id", "2", "--lang", "en")
    p = out["principles"][0]
    assert p["name"] == "Prin2"
    assert p["sub_principles"] == ["sub2a"]
    assert p["examples"] == ["ex2"]


def test_principle_duplicates_deduplicated(env):
    _, out, _ = run(env, "principle", "--id", "3,3")
    assert [p["id"] for p in out["principles"]] == [3]


# ----------------------------------------------------------------- param ---

def test_param_by_id(env):
    code, out, _ = run(env, "param", "--id", "9")
    assert code == 0
    p = out["parameters"][0]
    assert p["id"] == 9
    assert p["name"] == "파라미터9"
    assert p["definition"] == "정의9"
    assert p["keywords"] == ["속도", "speed"]


def test_param_by_id_en(env):
    _, out, _ = run(env, "param", "--id", "9", "--lang", "en")
    assert out["parameters"][0]["name"] == "Param9"
    assert out["parameters"][0]["definition"] == "def9"


def test_param_search_keyword(env):
    code, out, _ = run(env, "param", "--search", "속도")
    assert code == 0
    assert out["query"] == "속도"
    assert [m["id"] for m in out["matches"]] == [9]


def test_param_search_is_case_insensitive_and_matches_names(env):
    _, out, _ = run(env, "param", "--search", "SPEED")
    assert [m["id"] for m in out["matches"]] == [9]
    _, out, _ = run(env, "param", "--search", "param12")
    assert [m["id"] for m in out["matches"]] == [12]


def test_param_search_no_match_is_not_an_error(env):
    code, out, _ = run(env, "param", "--search", "zzzz")
    assert code == 0
    assert out["matches"] == []


# -------------------------------------------------------------- validate ---

def test_validate_ok_with_warning_for_missing_rows(env):
    code, out, err = run(env, "validate")
    assert code == 0 and err is None
    assert out["ok"] is True
    assert out["errors"] == []
    assert any(w["code"] == "missing_row" for w in out["warnings"])


def test_validate_no_warning_when_rows_complete(tmp_path):
    cells = {f"{r}-{1 if r != 1 else 2}": [1] for r in range(1, 40)}
    script = make_env(tmp_path, cells=cells, missing_rows=[])
    code, out, _ = run(script, "validate")
    assert code == 0
    assert out["warnings"] == []


@pytest.mark.parametrize("cells, needle", [
    ({"1-2": [41]}, "principle"),
    ({"1-2": [0]}, "principle"),
    ({"0-2": [1]}, "parameter"),
    ({"1-40": [1]}, "parameter"),
    ({"5-5": [1]}, "diagonal"),
    ({"1-2": []}, "empty"),
    ({"1-2": [3, 3]}, "duplicate"),
    ({"bad": [1]}, "key"),
])
def test_validate_detects_violations(tmp_path, cells, needle):
    script = make_env(tmp_path, cells=cells)
    code, out, err = run(script, "validate")
    assert code == 5
    assert err["error"]["code"] == "data_error"
    assert needle in json.dumps(err, ensure_ascii=False).lower()


def test_validate_detects_silent_missing_row(tmp_path):
    """A row with no cells that is not declared in missing_rows is an error."""
    script = make_env(tmp_path, cells={"1-2": [1]}, missing_rows=[])
    code, _, err = run(script, "validate")
    assert code == 5
    assert "missing_rows" in json.dumps(err, ensure_ascii=False)


def test_validate_detects_missing_name(tmp_path):
    script = make_env(tmp_path)
    p = tmp_path / "data" / "parameters.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    d["parameters"][3]["name"]["ko"] = ""
    write(p, d)
    code, _, err = run(script, "validate")
    assert code == 5


def test_validate_detects_wrong_principle_count(tmp_path):
    script = make_env(tmp_path)
    p = tmp_path / "data" / "inventive-principles.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    d["principles"].pop()
    write(p, d)
    code, _, _ = run(script, "validate")
    assert code == 5


def test_validate_missing_file_exit_5(tmp_path):
    script = make_env(tmp_path)
    (tmp_path / "data" / "parameters.json").unlink()
    code, _, err = run(script, "validate")
    assert code == 5
    assert err["error"]["code"] == "data_error"


# ------------------------------------------------------ unverified cells ---

def test_matrix_unverified_cell_reported_as_empty_with_warning(tmp_path):
    script = make_env(tmp_path, unverified=["1-17"])
    code, out, _ = run(script, "matrix", "--improve", "1", "--worsen", "17")
    assert code == 0
    assert out["pairs"] == []
    assert out["empty_pairs"] == [{"improve": 1, "worsen": 17}]
    assert out["warnings"] == [{"code": "unverified_cell", "improve": 1, "worsen": 17}]


def test_matrix_unverified_cell_does_not_affect_other_pairs(tmp_path):
    script = make_env(tmp_path, unverified=["1-17"])
    _, out, _ = run(script, "matrix", "--improve", "1", "--worsen", "2,17")
    assert [p["worsen"] for p in out["pairs"]] == [2]
    assert out["warnings"] == [{"code": "unverified_cell", "improve": 1, "worsen": 17}]


def test_validate_warns_about_unverified_cells(tmp_path):
    script = make_env(tmp_path, unverified=["1-17"])
    code, out, _ = run(script, "validate")
    assert code == 0
    assert {"code": "unverified_cell", "improve": 1, "worsen": 17} in out["warnings"]


def test_validate_rejects_unverified_cell_that_also_has_a_value(tmp_path):
    script = make_env(tmp_path, unverified=["1-2"])  # 1-2 exists in default cells
    code, _, err = run(script, "validate")
    assert code == 5
    assert "unverified_cells" in json.dumps(err, ensure_ascii=False)


@pytest.mark.parametrize("bad", ["x", "5-5", "0-3", "1-40"])
def test_validate_rejects_malformed_unverified_key(tmp_path, bad):
    script = make_env(tmp_path, unverified=[bad])
    code, _, err = run(script, "validate")
    assert code == 5
    assert "unverified_cells" in json.dumps(err, ensure_ascii=False)


# ------------------------------------------------ real data (smoke tests) ---

def _real_cells():
    return json.loads((REAL_DATA / "contradiction-matrix.json").read_text(encoding="utf-8"))["cells"]


def test_real_validate_passes():
    code, out, err = run(REAL_SCRIPT, "validate")
    assert code == 0, err
    assert out["ok"] is True


def test_real_matrix_matches_data_file_exactly():
    cells = _real_cells()
    improve = [1, 9]
    worsen = [2, 3, 14, 25]
    code, out, _ = run(REAL_SCRIPT, "matrix",
                       "--improve", ",".join(map(str, improve)),
                       "--worsen", ",".join(map(str, worsen)))
    assert code == 0
    for pair in out["pairs"]:
        assert pair["principles"] == cells[f"{pair['improve']}-{pair['worsen']}"]
    # every requested pair is accounted for exactly once, in exactly one bucket
    assert len(out["pairs"]) + len(out["empty_pairs"]) == len(improve) * len(worsen)
    for i in improve:
        for w in worsen:
            in_pairs = any(p["improve"] == i and p["worsen"] == w for p in out["pairs"])
            assert in_pairs == (f"{i}-{w}" in cells)


def test_real_matrix_flags_declared_gaps():
    data = json.loads((REAL_DATA / "contradiction-matrix.json").read_text(encoding="utf-8"))
    for row in data["missing_rows"]:
        code, out, _ = run(REAL_SCRIPT, "matrix", "--improve", str(row), "--worsen", "1")
        assert code == 0
        assert {"code": "missing_row", "improve": row} in out["warnings"]
    for key in data["unverified_cells"]:
        i, w = key.split("-")
        code, out, _ = run(REAL_SCRIPT, "matrix", "--improve", i, "--worsen", w)
        assert code == 0
        assert out["pairs"] == [] and out["empty_pairs"] == [{"improve": int(i), "worsen": int(w)}]
        assert {"code": "unverified_cell", "improve": int(i), "worsen": int(w)} in out["warnings"]


def test_real_principle_all_40_resolve():
    code, out, _ = run(REAL_SCRIPT, "principle", "--id", ",".join(str(i) for i in range(1, 41)))
    assert code == 0
    assert len(out["principles"]) == 40


def test_real_param_all_39_resolve():
    for i in (1, 20, 39):
        code, out, _ = run(REAL_SCRIPT, "param", "--id", str(i))
        assert code == 0
        assert out["parameters"][0]["id"] == i


def test_output_is_utf8_json_not_escaped():
    proc = subprocess.run([sys.executable, str(REAL_SCRIPT), "principle", "--id", "1"],
                          capture_output=True)
    assert "분할".encode("utf-8") in proc.stdout
