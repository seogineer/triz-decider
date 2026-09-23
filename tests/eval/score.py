#!/usr/bin/env python3
"""Score an eval run (DESIGN 10.1). Stdlib only.

Usage: python tests/eval/score.py results.json

results.json maps case id -> {"improve": [ids ranked best-first],
"worsen": [ids ranked best-first], "principles_cited": [ids]}.

- A side "hits" if any expected id is among that side's top-3 candidates.
- A case hits if both sides hit.
- A cited principle is a hallucination if it is not in the ranking that
  lookup.py returns for the run's own candidate pairs.
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOOKUP = HERE.parent.parent / "skills" / "triz-analysis" / "scripts" / "lookup.py"
TOP_N = 3


def real_matrix(improve, worsen):
    """Return the set of principle ids lookup.py ranks, or None if it errors."""
    p = subprocess.run(
        [sys.executable, str(LOOKUP), "matrix",
         "--improve", ",".join(map(str, improve)), "--worsen", ",".join(map(str, worsen))],
        capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        return None
    return {r["id"] for r in json.loads(p.stdout)["ranking"]}


def score(cases, results, matrix=real_matrix):
    rows, hits, imp_hits, wor_hits, halluc, missing = [], 0, 0, 0, 0, []
    for c in cases:
        r = results.get(c["id"])
        if r is None:
            missing.append(c["id"])
            continue
        imp, wor = r["improve"][:TOP_N], r["worsen"][:TOP_N]
        ih = bool(set(imp) & set(c["expected_improve"]))
        wh = bool(set(wor) & set(c["expected_worsen"]))
        allowed = matrix(imp, wor)
        cited = list(r.get("principles_cited", []))
        bad = cited if allowed is None else [p for p in cited if p not in allowed]
        hits += ih and wh
        imp_hits += ih
        wor_hits += wh
        halluc += len(bad)
        rows.append({"id": c["id"], "improve_hit": ih, "worsen_hit": wh,
                     "hit": ih and wh, "hallucinated_principles": bad})
    n = len(rows)
    return {"cases_scored": n, "cases_missing": missing,
            "top3_hit_rate": hits / n if n else 0.0,
            "improve_hit_rate": imp_hits / n if n else 0.0,
            "worsen_hit_rate": wor_hits / n if n else 0.0,
            "hallucinated_principles": halluc, "rows": rows}


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    cases = json.loads((HERE / "cases.yaml").read_text(encoding="utf-8"))["cases"]
    results = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    print(json.dumps(score(cases, results), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
