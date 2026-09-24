# Changelog

## 0.1.1 — 2026-09-24
Data fix: the contradiction matrix now comes from a 2-of-3 vote of three independently transcribed sources (English transcription family, MATRIZ Knowledge Base, Russian-language table).
- 15 cells changed value versus 0.1.0 (1-27, 4-16, 9-1, 9-29, 13-18, 14-33, 14-36, 17-23, 19-9, 26-28, 29-7, 34-14, 37-10, 37-21, 39-33). In 0.1.0 these carried the English transcription's values, which both other sources contradict.
- 9 cells that 0.1.0 withheld are now filled (1-28, 1-38, 7-28, 8-25, 15-25, 15-31, 18-35, 33-10, 34-1). No cell is withheld any more.
- `/triz` now tells Claude to load `triz-decider:triz-analysis` explicitly and not to answer from memory (fixes runs that skipped the skill).
- Eval: 33 cases, blind runs, and an observed-lookup hallucination check. See `tests/eval/results-v0.1.md`.

## 0.1.0 — 2026-09-24
First release: technical-contradiction flow, `lookup.py`, 39 parameters, 40 principles, contradiction matrix.
