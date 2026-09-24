#!/usr/bin/env python3
"""Compare the plugin with TRIZBench patent labels (Zhu et al., ACL Findings 2026).

The dataset is used locally only and is never stored in this repo: pass its
`patent_task1_classical.jsonl` with --data. Metric follows the paper's Hit@3:
the gold (improving, worsening) pair must be among the first three ranked pairs.

Usage:
  python tests/eval/trizbench_eval.py --data PATH --n 30 --seed 20260924 --run
  python tests/eval/trizbench_eval.py --data PATH --score OUTDIR/results.json
"""
import argparse
import ast
import itertools
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TWINS = {2: 1, 4: 3, 6: 5, 8: 7, 16: 15, 20: 19}  # stationary -> moving counterpart
TOP_N = 3


def load_records(path):
    kept = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        gold = r["gold_json"]
        gold = ast.literal_eval(gold) if isinstance(gold, str) else gold
        plus, minus = gold.get("plus_ids", []), gold.get("minus_ids", [])
        text = (r.get("input_text") or "").strip()
        if len(plus) != 1 or len(minus) != 1 or not text:
            continue
        if not (1 <= plus[0] <= 39 and 1 <= minus[0] <= 39) or plus[0] == minus[0]:
            continue
        kept.append({"patent_id": r["patent_id"], "gold": (plus[0], minus[0]), "text": text})
    return kept


def sample(records, n, seed):
    if n >= len(records):
        return list(records)
    return random.Random(seed).sample(records, n)


def to_cases(records, max_chars=3000):
    """One case per patent id (the dataset repeats some patents)."""
    seen, cases = set(), []
    for r in records:
        if r["patent_id"] in seen:
            continue
        seen.add(r["patent_id"])
        cases.append({"id": r["patent_id"], "lang": "en", "problem": r["text"][:max_chars]})
    return cases


def _valid(res):
    return bool(res and res.get("plugin_loaded") and res.get("exit_code") == 0
                and res.get("improve") and res.get("worsen"))


def pending_cases(cases, existing):
    """Cases that still need a run: never run, or failed for infrastructure reasons."""
    return [c for c in cases if not _valid(existing.get(c["id"]))]


def rank_pairs(improve, worsen):
    """Candidate pairs, best first: lowest rank sum, ties by improving rank."""
    pairs = [(i, w, ri + rw, ri) for (ri, i), (rw, w) in
             itertools.product(enumerate(improve), enumerate(worsen)) if i != w]
    pairs.sort(key=lambda p: (p[2], p[3]))
    return [(i, w) for i, w, _, _ in pairs]


def _fam(x):
    return TWINS.get(x, x)


def metrics(gold, improve, worsen):
    gi, gw = gold
    ranked = rank_pairs(improve, worsen)
    top = ranked[:TOP_N]
    fam_top = [(_fam(i), _fam(w)) for i, w in top]
    return {"improve_hit": gi in improve[:TOP_N], "worsen_hit": gw in worsen[:TOP_N],
            "pair_lenient": gi in improve[:TOP_N] and gw in worsen[:TOP_N],
            "hit3": (gi, gw) in top, "hit3_family": (_fam(gi), _fam(gw)) in fam_top,
            "top1": bool(ranked) and ranked[0] == (gi, gw)}


def summarize(rows):
    n = len(rows)
    keys = ["improve_hit", "worsen_hit", "pair_lenient", "hit3", "hit3_family", "top1"]
    return {"n": n, **{k: (sum(r[k] for r in rows) / n if n else 0.0) for k in keys}}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--seed", type=int, default=20260924)
    ap.add_argument("--run", action="store_true", help="run the plugin blind on the sample")
    ap.add_argument("--score", help="results.json from a run")
    ap.add_argument("--out", default=str(HERE / "trizbench-run"))
    ap.add_argument("--jobs", type=int, default=3)
    a = ap.parse_args(argv)
    records = sample(load_records(a.data), a.n, a.seed)
    if a.run:
        import tempfile
        from concurrent.futures import ThreadPoolExecutor
        sys.path.insert(0, str(HERE))
        import run_blind as rb
        out = Path(a.out); raw = out / "raw"; raw.mkdir(parents=True, exist_ok=True)
        results_path = out / "results.json"
        existing = json.loads(results_path.read_text(encoding="utf-8")) if results_path.exists() else {}
        cases = pending_cases(to_cases(records), existing)
        print(json.dumps({"to_run": len(cases), "already_valid": len(existing) - len(cases) if existing else 0}))
        with tempfile.TemporaryDirectory() as tmp:
            plugin, work = Path(tmp) / "plugin", Path(tmp) / "work"
            work.mkdir(); rb.make_plugin_copy(plugin)
            with ThreadPoolExecutor(a.jobs) as ex:
                done = list(ex.map(lambda c: rb.run_case(c, "command", plugin, work, raw), cases))
        existing.update(dict(done))
        results_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
        a.score = str(results_path)
    if a.score:
        res = json.loads(Path(a.score).read_text(encoding="utf-8"))
        rows, invalid = [], []
        for r in records:
            p = res.get(r["patent_id"])
            if not _valid(p):
                invalid.append(r["patent_id"]); continue
            rows.append(metrics(r["gold"], p["improve"], p["worsen"]))
        print(json.dumps({"summary": summarize(rows), "invalid_or_unparsed": invalid}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
