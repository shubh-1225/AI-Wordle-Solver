# Experiments

## Objective

Measure how a **greedy Shannon-entropy Wordle policy** performs as a full six-turn solver on the original answer list, and whether the opening word with highest first-guess entropy also yields the lowest average guess count.

## Experimental setup

| Item | Value |
| --- | --- |
| Answers | `data/answers.txt`, **2,315** words |
| Allowed guesses | `data/allowed_guesses.txt`, **12,972** words |
| Fingerprints | SHA-256 in `benchmarks/results/opener_results.json` |
| Feedback | two-pass engine in `app/solver/feedback.py` |
| Policy after turn 1 | `maximum_entropy` (one-ply) |
| Hard mode | off |
| Max guesses | 6 |
| Failures | counted as 7 for `average_guesses_failures_as_7` |
| Cache | `cache/feedback_patterns.npz` when present |
| Openers | five allowed words with highest first-guess entropy: `soare`, `roate`, `raise`, `raile`, `reast` |
| Command | `python scripts/find_best_openers.py --top-entropy 5 --strategy maximum_entropy` |
| Generated | 2026-10-04T21:23:39Z UTC |

Hardware was not recorded beyond wall-clock time per opener (~93–95 s) on the machine that wrote the JSON. Software: this repository’s Python solver with NumPy cache.

Randomness: **none** for these runs. Given the lists, strategy, and opener, play is deterministic.

The `candidate_reduction` objective exists in code. It was **not** swept on all 2,315 answers for this report.

## Metrics

- Average / median / minimum / maximum guesses among wins
- Average guesses with failures as 7
- Win rate within 6
- Guess-count histogram (1–6 and failed)
- First-guess Shannon entropy (bits)
- Wall-clock seconds per opener

Candidate reduction by turn is visible inside a single `simulate()` trace (GUI solver mode / Assist stats). The published opener JSON stores end-of-game histograms, not per-turn mean |C|.

## Experimental results

Source: [`benchmarks/results/opener_results.json`](../benchmarks/results/opener_results.json)

| Rank | Opener | Answer word? | H₁ (bits) | Avg | Median | Worst | Win rate | 2 | 3 | 4 | 5 | 6 | Fail |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | reast | no | 5.865 | 3.4371 | 3 | 5 | 100% | 69 | 1221 | 969 | 56 | 0 | 0 |
| 2 | soare | no | 5.886 | 3.4648 | 3 | 6 | 100% | 44 | 1216 | 991 | 63 | 1 | 0 |
| 3 | roate | no | 5.883 | 3.4674 | 3 | 5 | 100% | 54 | 1170 | 1046 | 45 | 0 | 0 |
| 4 | raile | no | 5.866 | 3.4687 | 3 | 5 | 100% | 50 | 1177 | 1041 | 47 | 0 | 0 |
| 5 | raise | yes | 5.878 | 3.4717 | 3 | 6 | 100% | 57 | 1173 | 1019 | 63 | 2 | 0 |

`raise` additionally has **1** win in one guess (the hidden answer was `raise`).

An independent `simulate()` sweep of all 2,315 answers with opener `soare` produced the same histogram 44 / 1216 / 991 / 63 / 1, which checks the grouped opener benchmark against per-answer simulation.

First-guess metrics for `soare` on the full answer list (live solver, cache on): **H = 5.886 bits**, **127** nonempty pattern groups, expected remaining **62.3** candidates (~97.3% expected reduction).

## Analysis

All five openers solve every original answer within six guesses under maximum entropy. The spread in averages is small (about 0.035 guesses). The best average (`reast`) is **not** the best opening entropy (`soare`). That is the expected gap between greedy information at ply one and realized length of the full trajectory.

Non-answer probes occupy four of the five slots. Using only remaining answers as guesses would exclude the empirically best openers on this list.

Worst-case answers cluster on repeated letters and uncommon consonants (`waver` is the unique 6-guess `soare` game). Entropy still wins those games, but partitions become coarse late.

Runtime of ~1.5 minutes per opener with the cache is acceptable for a 2,315 × remaining-pool ranking loop; without the matrix the same experiment is dominated by Python feedback calls.

## Conclusions

1. A greedy entropy solver with the original dictionaries is a complete (100% win) Wordle policy for these five openers.
2. Opening entropy is a useful shortlist criterion, not a sufficient statistic for average game length.
3. Allowing non-answer guesses matters.
4. Precomputed ternary feedback is an engineering prerequisite for exhaustive evaluation, not a change in the mathematical policy.

No claim is made about the live NYT list, hard mode, or optimality among all 12,972 possible openers (only the top-five entropy shortlist was fully simulated).
