# Changelog

## 0.1.2 — 2026-09-24
- **Renamed the plugin slug `triz-decider` → `triz-solver`** (display name TRIZ Solver). Commands are now `/triz-solver:triz`; reinstall with `/plugin install triz-solver@triz-solver`. The plugin derives solution ideas rather than making a decision, and the slug can still change before directory listing.
- README (en/ko) now states the scope: the plugin expects an input that names the trade-off; it does not dig a contradiction out of a solution description. A "not covered" section lists what is not implemented (physical contradictions, interview flow).
- Skill description adds Korean trigger keywords (기술적 모순, 물리적 모순, 모순 행렬, 발명원리).
- Eval: compared against the TRIZBench patent benchmark (`tests/eval/trizbench_eval.py`). Hit@3 is 3/30 = 10%, chance level and below a constant baseline of 13%. The dataset is not stored in the repo (no license).
- Eval: revised 9 flagged expected values in `cases.yaml` (C03, C09, C17, C18, C21, C22, C23, C26; C28 dropped); C22 and C26 are marked `expect_empty`. All earlier runs are rescored: 91/93 Top-3. `tests/eval/review-expected-values.md` lists the cases for a third-party review.
- Author name unified as DoGyeong Seo across licenses and manifests.

## 0.1.1 — 2026-09-24
Data fix: the contradiction matrix now comes from a 2-of-3 vote of three independently transcribed sources (English transcription family, MATRIZ Knowledge Base, Russian-language table).
- 15 cells changed value versus 0.1.0 (1-27, 4-16, 9-1, 9-29, 13-18, 14-33, 14-36, 17-23, 19-9, 26-28, 29-7, 34-14, 37-10, 37-21, 39-33). In 0.1.0 these carried the English transcription's values, which both other sources contradict.
- 9 cells that 0.1.0 withheld are now filled (1-28, 1-38, 7-28, 8-25, 15-25, 15-31, 18-35, 33-10, 34-1). No cell is withheld any more.
- `/triz` now tells Claude to load `triz-decider:triz-analysis` explicitly and not to answer from memory (fixes runs that skipped the skill).
- Eval: 33 cases, blind runs, and an observed-lookup hallucination check. See `tests/eval/results-v0.1.md`.

## 0.1.0 — 2026-09-24
First release: technical-contradiction flow, `lookup.py`, 39 parameters, 40 principles, contradiction matrix.
