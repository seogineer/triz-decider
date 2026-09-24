# TRIZ Solver

[한국어](README.ko.md)

A Claude Code plugin that helps you resolve engineering and product trade-offs with **TRIZ**: it turns a problem into a technical contradiction, looks up the classic contradiction matrix, and proposes ideas from the 40 inventive principles.

No server, database or API key. Claude does the reasoning; a small standard-library Python script does every lookup, so matrix cells and principle numbers are never recalled from memory.

> **Status: v0.1 (pre-release).** Technical contradictions only. Physical contradictions and the guided interview come in v0.2. See [Data status](#data-status) before relying on results.

## Install

```
/plugin marketplace add seogineer/triz-solver
/plugin install triz-solver@triz-solver
```

To try it from a local checkout: `claude --plugin-dir .`

## Use

```
/triz Raising the top speed of my e-scooter drains the battery too fast
```

If `/triz` is not recognised in your session, use the full name `/triz-solver:triz`.

You can also just describe a trade-off in plain language (English or Korean); the `triz-analysis` skill activates on its own. The answer follows the language you write in.

The flow:

1. Restate the problem as "improving X worsens Y" and confirm it with you
2. Map X and Y to the 39 engineering parameters (1–3 candidates each, with reasons)
3. Look up every candidate pair in the matrix (`lookup.py matrix`)
4. Rank principles by how often they appear
5. Fetch each principle's definition (`lookup.py principle`)
6. Write ideas tailored to your system, one to three per principle

**Works best when you state the trade-off yourself** ("improving X makes Y worse"). It is not built to dig a contradiction out of a text that only describes a solution, such as a patent abstract; see the benchmark note under Data status.

## How it works

| Step | Done by |
| --- | --- |
| Understanding the problem, mapping to parameters, writing ideas | Claude |
| Parameter/principle validation, matrix lookup, ranking | `skills/triz-analysis/scripts/lookup.py` |

`lookup.py` (Python 3.9+, standard library only, no network) prints JSON:

```
python3 skills/triz-analysis/scripts/lookup.py matrix --improve 9 --worsen 19,22
python3 skills/triz-analysis/scripts/lookup.py principle --id 35,15
python3 skills/triz-analysis/scripts/lookup.py param --search speed --lang en
python3 skills/triz-analysis/scripts/lookup.py validate
```

Errors are JSON on stderr with exit codes 2 (bad argument), 3 (id out of range), 4 (same parameter), 5 (data error). An empty matrix cell is not an error; it is reported in `empty_pairs`.

The skill folder is self-contained (`data/` and `scripts/` live inside it), so it can also be uploaded on its own to Claude.ai.

## What it does not cover

TRIZ is much broader than this plugin. v0.1 only does the technical-contradiction route (contradiction matrix, then the 40 inventive principles). It does **not** do:

- problem analysis before the contradiction is known: function analysis, trimming, root-cause and hidden-resource analysis
- the 76 standard solutions and substance-field analysis
- ARIZ, technology evolution laws, or functional-oriented search
- physical contradictions and the guided interview (planned for v0.2)

The 40 principles are a checklist for generating ideas, not a guarantee. If the results feel off, the mapping or the problem definition usually needs another look before the principles do.

## Data status

| Data | Status |
| --- | --- |
| Contradiction matrix | all 1248 cells settled by a 2-of-3 vote of three independently transcribed sources (an English transcription family, the MATRIZ Knowledge Base, a Russian-language table). Nothing is withheld now; the `unverified_cell` warning remains for any future dispute. Not yet compared with a printed original. |
| 39 parameters, 40 principles | Numbers and names cross-checked; definitions, sub-principles and examples written for this project |
| Mapping accuracy | 32 blind-run cases: Top-3 hit rate 96-100% across runs (91/93 overall after the expected values were revised), 0 hallucinated principle numbers, and 9/9 disclosures when a withheld cell was hit. Small set with author-written expected values and some run-to-run variation, so treat it as a smoke test. **On an independent patent benchmark (TRIZBench) the plugin scored Hit@3 = 10% on the first 30 patents and 13% on 75 held-out patents, about the level of always guessing the three most common answers (9-16%)**: it works best when you state the trade-off yourself, not when the input only describes a solution (see `tests/eval/results-v0.1.md`) |

Sources, method and the disputed cells are listed in [DATA_SOURCES.md](DATA_SOURCES.md). TRIZ output is a source of ideas, not a verdict: check the mapping and validate ideas before acting on them.

## Development

```
pip install pytest
pytest tests/
python skills/triz-analysis/scripts/lookup.py validate
claude plugin validate .
```

## License

Code (scripts, tests, manifests): [MIT](LICENSE). Text written for this project (parameter definitions, principle descriptions, examples): CC BY 4.0, see [LICENSE-DATA.md](LICENSE-DATA.md). Matrix cell values follow the classic Altshuller matrix and are credited in DATA_SOURCES.md.
