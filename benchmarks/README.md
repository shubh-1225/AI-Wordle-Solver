# Benchmark artifacts

This folder holds **solver evaluation**, not GUI session statistics.

```text
benchmarks/
├── README.md                 (this file)
├── raw/                      empty on purpose (see below)
├── results/
│   ├── opener_results.json   published source of truth
│   ├── starting_word_results.csv
│   └── guess_distribution.csv
└── figures/
    ├── average_guesses_by_opener.svg
    ├── opener_entropy.svg
    └── soare_guess_distribution.svg
```

## Source of truth

`results/opener_results.json` was produced by:

```bash
python scripts/find_best_openers.py --top-entropy 5 --strategy maximum_entropy
```

on 2,315 answers, strategy `maximum_entropy`, generated 2026-10-04T21:23:39Z.

Regenerate tables and figures after replacing that JSON:

```bash
python scripts/export_benchmark_artifacts.py
```

## Raw traces

Per-answer guess lists for 2,315 × 5 openers would be a large, redundant dump of what the JSON already aggregates. They are not committed. `scripts/benchmark_solver.py` prints a live summary; add your own logging if you need traces locally.

## Solver Benchmark Report

Dataset: 2,315 answer words, 12,972 allowed guesses.

Strategy for later guesses: maximum entropy.

| Starting word | Avg | Median | Worst | Win rate |
| --- | ---: | ---: | ---: | ---: |
| reast | 3.437 | 3 | 5 | 100% |
| soare | 3.465 | 3 | 6 | 100% |
| roate | 3.467 | 3 | 5 | 100% |
| raile | 3.469 | 3 | 5 | 100% |
| raise | 3.472 | 3 | 6 | 100% |

### Interpretation

On the original Wordle answer list this greedy policy is complete for these five openers: every game finishes in six or fewer guesses. The best opening entropy (`soare`, 5.886 bits) is slightly worse as a full-game average than `reast` (3.437 vs 3.465). That is a one-ply vs full-horizon gap, not a measurement error: the `soare` histogram independently matched a per-answer `simulate()` sweep (44 / 1216 / 991 / 63 / 1).

`candidate_reduction` can be selected in code and in the GUI but has no published full-dictionary table in this folder.
