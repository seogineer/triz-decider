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


def test_cases_have_unique_ids():
    assert len(CASES) >= 20
    assert len({c["id"] for c in CASES}) == len(CASES)


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_case_is_well_formed(case):
    assert case["problem"].strip()
    assert case["lang"] in ("ko", "en")
    for key in ("expected_improve", "expected_worsen"):
        assert case[key] and all(1 <= x <= 39 for x in case[key])
    assert not set(case["expected_improve"]) & set(case["expected_worsen"])


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_expected_pair_matches_case_kind(case):
    """Normal cases must be answerable from verified data; expect_unverified
    cases must land exactly on withheld cells (and nothing else)."""
    import subprocess, sys
    p = subprocess.run(
        [sys.executable, str(score_mod.LOOKUP), "matrix",
         "--improve", ",".join(map(str, case["expected_improve"])),
         "--worsen", ",".join(map(str, case["expected_worsen"]))],
        capture_output=True, text=True, encoding="utf-8")
    out = json.loads(p.stdout)
    if case.get("expect_unverified"):
        assert out["pairs"] == [], f"{case['id']}: expected only withheld cells"
        assert any(w["code"] == "unverified_cell" for w in out["warnings"])
    else:
        assert out["ranking"], f"{case['id']}: expected pair gives no principles"


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


# ------------------------------------------------------- blind-run parser ---

spec2 = importlib.util.spec_from_file_location("run_blind", EVAL / "run_blind.py")
run_blind = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(run_blind)

ANSWER_KO = """## 파라미터 매핑
| 구분 | 파라미터 | 근거 |
| --- | --- | --- |
| 개선 | #9 속도 | 빠르기 |
| 개선 | #39 생산성 | 산출량 |
| 악화 | #29 제조 정밀도 | 자국 |
| 악화 | #9 속도 | 중복은 무시 |

## 추천 원리 (행렬 조회 결과)
| 1 | #10 사전 조치 | 2 |

## 적용 아이디어
### 원리 #10 사전 조치
- 아이디어
### 원리 #35 매개변수 변화
- 아이디어
### 원리 #10 사전 조치
"""

ANSWER_EN = """| Improve | #9 Speed | x |
| Worsen | #23 Loss of substance | y |
### Principle #35 Parameter changes
"""


def test_parse_answer_korean():
    r = run_blind.parse_answer(ANSWER_KO)
    assert r["improve"] == [9, 39]
    assert r["worsen"] == [29, 9]
    assert r["principles_cited"] == [10, 35]  # ranking-table rows are not "cited"


def test_parse_answer_english():
    r = run_blind.parse_answer(ANSWER_EN)
    assert r == {"improve": [9], "worsen": [23], "principles_cited": [35]}


def test_parse_stream_extracts_tool_calls_and_result():
    lines = [
        json.dumps({"type": "system", "subtype": "init", "plugins": [{"name": "triz-decider"}], "slash_commands": []}),
        json.dumps({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Skill", "input": {"skill": "triz-decider:triz-analysis"}},
            {"type": "tool_use", "name": "Bash", "input": {"command": "python3 x/lookup.py matrix --improve 1 --worsen 2"}},
            {"type": "tool_use", "name": "Bash", "input": {"command": "ls"}}]}}),
        "not json",
        json.dumps({"type": "result", "result": "final text"}),
    ]
    info = run_blind.parse_stream(lines)
    assert info["plugin_loaded"] and info["skill_used"]
    assert info["lookup_calls"] == 1
    assert info["text"] == "final text"


def test_parse_stream_command_alone_is_not_skill_use():
    """Invoking the /triz command without loading triz-analysis must not count."""
    lines = [json.dumps({"type": "system", "subtype": "init", "plugins": [{"name": "triz-decider"}], "slash_commands": []}),
             json.dumps({"type": "assistant", "message": {"content": [
                 {"type": "tool_use", "name": "Skill", "input": {"skill": "triz-decider:triz"}}]}}),
             json.dumps({"type": "result", "result": "x"})]
    assert run_blind.parse_stream(lines)["skill_used"] is False


def test_parse_stream_detects_missing_plugin_and_skill():
    lines = [json.dumps({"type": "system", "subtype": "init", "plugins": [], "slash_commands": ["help"]}),
             json.dumps({"type": "result", "result": "answer from memory"})]
    info = run_blind.parse_stream(lines)
    assert not info["plugin_loaded"] and not info["skill_used"] and info["lookup_calls"] == 0


def test_build_prompt_modes():
    case = {"problem": "P", "lang": "en"}
    assert run_blind.build_prompt(case, "command").startswith("/triz-decider:triz P")
    assert run_blind.build_prompt(case, "natural").startswith("P")


def test_parse_answer_empty():
    assert run_blind.parse_answer("") == {"improve": [], "worsen": [], "principles_cited": []}


def test_plugin_copy_excludes_expected_values(tmp_path):
    run_blind.make_plugin_copy(tmp_path)
    assert (tmp_path / "skills" / "triz-analysis" / "SKILL.md").exists()
    assert not (tmp_path / "tests").exists()
    assert not any(tmp_path.rglob("cases.yaml"))


# ------------------------------------------- unverified-cell disclosure ---

def test_parse_stream_sees_unverified_warning_in_tool_result():
    lines = [
        json.dumps({"type": "system", "subtype": "init", "plugins": [{"name": "triz-decider"}], "slash_commands": []}),
        json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "content": '{"warnings": [{"code": "unverified_cell", "improve": 1, "worsen": 28}]}'}]}}),
        json.dumps({"type": "result", "result": "ok"}),
    ]
    assert run_blind.parse_stream(lines)["saw_unverified"] is True
    assert run_blind.parse_stream(lines[:1] + lines[2:])["saw_unverified"] is False


@pytest.mark.parametrize("text, expected", [
    ("이 조합은 검증된 데이터가 없어 조회할 수 없습니다.", True),
    ("Cell is unverified in the dataset, so I cannot look it up.", True),
    ("해당 셀은 미확정이라 원리를 추천하지 않습니다.", True),
    ("추천 원리는 #10, #35 입니다.", False),
])
def test_discloses_unverified(text, expected):
    assert run_blind.discloses_unverified(text) is expected


def test_score_unverified_disclosure_summary():
    cases = [{"id": "U1", "expected_improve": [1], "expected_worsen": [28], "expect_unverified": True},
             {"id": "U2", "expected_improve": [34], "expected_worsen": [1], "expect_unverified": True},
             {"id": "N1", "expected_improve": [9], "expected_worsen": [27]}]
    results = {
        "U1": {"improve": [1], "worsen": [28], "principles_cited": [], "saw_unverified": True, "disclosed": True},
        "U2": {"improve": [34], "worsen": [1], "principles_cited": [], "saw_unverified": True, "disclosed": False},
        "N1": {"improve": [9], "worsen": [27], "principles_cited": [], "saw_unverified": False, "disclosed": False},
    }
    out = score_mod.score(cases, results, matrix=fake_matrix)
    u = out["unverified"]
    assert u == {"cases_with_warning": 2, "disclosed": 1, "not_disclosed": ["U2"]}


# --------------------------------- principles actually returned by lookup ---

def _tool_result(payload):
    return json.dumps({"type": "user", "message": {"content": [
        {"type": "tool_result", "content": [{"type": "text", "text": json.dumps(payload)}]}]}})


def test_parse_stream_collects_principles_returned_by_lookup():
    lines = [
        json.dumps({"type": "system", "subtype": "init", "plugins": [{"name": "triz-decider"}], "slash_commands": []}),
        _tool_result({"pairs": [{"improve": 34, "worsen": 26, "principles": [2, 28, 10, 25]}],
                      "ranking": [{"id": 2, "count": 1, "name": "x"}], "warnings": []}),
        _tool_result({"principles": [{"id": 35, "name": "y"}]}),
        _tool_result({"unrelated": [7, 8]}),
    ]
    info = run_blind.parse_stream(lines)
    assert info["returned_principles"] == [2, 10, 25, 28, 35]


def test_score_prefers_observed_lookup_output_over_recomputation():
    cases = [{"id": "A", "expected_improve": [34], "expected_worsen": [1]}]
    results = {"A": {"improve": [34], "worsen": [1], "principles_cited": [2, 25, 99],
                     "returned_principles": [2, 25, 28]}}
    # recomputation from the reported candidates would allow nothing; observed output allows 2 and 25
    out = score_mod.score(cases, results, matrix=lambda i, w: set())
    assert out["rows"][0]["hallucinated_principles"] == [99]
