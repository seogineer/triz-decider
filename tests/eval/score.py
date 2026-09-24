#!/usr/bin/env python3
"""Score an eval run (DESIGN 10.1). Stdlib only.

Usage: python tests/eval/score.py results.json

results.json maps case id -> {"improve": [ids ranked best-first],
"worsen": [ids ranked best-first], "principles_cited": [ids]}.

- A side "hits" if any expected id is among that side's top-3 candidates.
- A case hits if both sides hit.
- "unverified": among runs whose lookup output carried an unverified_cell
  warning (observed in the tool result), how many told the user so.
- A cited principle is a hallucination if lookup.py did not return it in that
  run (observed in the tool results; older result files without that field
  fall back to recomputing from the reported candidate pairs).
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
        # Prefer what lookup.py actually returned in this run (observed); fall back
        # to recomputing from the reported candidates for older result files.
        observed = r.get("returned_principles")
        allowed = set(observed) if observed is not None else matrix(imp, wor)
        cited = list(r.get("principles_cited", []))
        bad = cited if allowed is None else [p for p in cited if p not in allowed]
        hits += ih and wh
        imp_hits += ih
        wor_hits += wh
        halluc += len(bad)
        rows.append({"id": c["id"], "improve_hit": ih, "worsen_hit": wh,
                     "hit": ih and wh, "hallucinated_principles": bad})
    n = len(rows)
    warned = [c["id"] for c in cases if c["id"] in results and results[c["id"]].get("saw_unverified")]
    undisclosed = [i for i in warned if not results[i].get("disclosed")]
    return {"unverified": {"cases_with_warning": len(warned),
                           "disclosed": len(warned) - len(undisclosed),
                           "not_disclosed": undisclosed},
            **_summary(rows, n, hits, imp_hits, wor_hits, halluc, missing)}


def _summary(rows, n, hits, imp_hits, wor_hits, halluc, missing):
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
