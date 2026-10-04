# Benchmarks

Published numbers come from this repository’s word lists and solver. They are **not** a claim that any starting word is universally optimal for Wordle.

## Word lists

- Answers: `data/answers.txt` (2,315 original Wordle answers)
- Allowed guesses: `data/allowed_guesses.txt` (12,972 words, including all answers)
- Provenance: `docs/DATASET.md` and `data/README.md`

Changing either file changes opener rankings. Compare results only when the SHA-256 fingerprints in the JSON match.

## Solver

After the first guess, later guesses use the named strategy.

- Strategy for the published table: `maximum_entropy`
- Also implemented: `candidate_reduction` (minimize expected remaining candidates)
- Feedback: two-pass coloring in `app/solver/feedback.py`
- Candidate set: remaining answers consistent with all feedback so far
- Guess pool: unused words from the allowed-guess list
- Cache: `cache/feedback_patterns.npz` when present
- Hard mode: not used
- Maximum guesses: 6
- Failures: counted as 7 for `average_guesses_failures_as_7`

The solver is deterministic for a given opener, answer, strategy, and word lists. No seed is required.

## Opener procedure

`scripts/find_best_openers.py`:

1. Optionally take the N allowed guesses with highest first-guess Shannon entropy (`--top-entropy`).
2. Optionally add `--openers`.
3. For each selected starting word, play it as guess 1 against **every** answer and choose later guesses with the selected strategy.
4. Rank by average guesses (failures as 7), then average among wins, win rate, worst case, then spelling.

Answers that share a feedback history share a remaining set; the implementation groups those paths. That is equivalent to `simulate(answer, starting_word=opener)` once per answer.

## How to reproduce

```bash
python scripts/precompute_patterns.py
python scripts/find_best_openers.py --top-entropy 5 --strategy maximum_entropy
python scripts/export_benchmark_artifacts.py
```

Default JSON path: `benchmarks/results/opener_results.json`

Single-opener sweep (prints a summary; does not overwrite the published JSON unless you add your own redirection):

```bash
python scripts/benchmark_solver.py --opener soare --strategy maximum_entropy
```

`--limit` on the single-opener script is a development shortcut, not the published ranking.

## Results

Source of truth: [`benchmarks/results/opener_results.json`](../benchmarks/results/opener_results.json)

Generated: 2026-10-04T21:23:39Z UTC  
Strategy: `maximum_entropy`  
Answers: 2,315  
Allowed guesses: 12,972  
Selected set: five highest first-guess-entropy allowed words (`soare`, `roate`, `raise`, `raile`, `reast`)

| Rank | Opener | In answer list | H₁ (bits) | Avg guesses | Median | Worst | Win rate | 1 | 2 | 3 | 4 | 5 | 6 | Failed |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | reast | no | 5.865 | 3.4371 | 3 | 5 | 100% | 0 | 69 | 1221 | 969 | 56 | 0 | 0 |
| 2 | soare | no | 5.886 | 3.4648 | 3 | 6 | 100% | 0 | 44 | 1216 | 991 | 63 | 1 | 0 |
| 3 | roate | no | 5.883 | 3.4674 | 3 | 5 | 100% | 0 | 54 | 1170 | 1046 | 45 | 0 | 0 |
| 4 | raile | no | 5.866 | 3.4687 | 3 | 5 | 100% | 0 | 50 | 1177 | 1041 | 47 | 0 | 0 |
| 5 | raise | yes | 5.878 | 3.4717 | 3 | 6 | 100% | 1 | 57 | 1173 | 1019 | 63 | 2 | 0 |

Highest first-guess entropy (`soare`) was not the lowest full-game average (`reast`).

Tables and figures derived from that JSON:

- `benchmarks/results/starting_word_results.csv`
- `benchmarks/results/guess_distribution.csv`
- `benchmarks/figures/*.svg`

## Game statistics vs solver benchmarks

The GUI Game Statistics panel is **session state** (current guess number, remaining candidates, cumulative entropy from turns in that game). It is not a log of the author’s personal Wordle streak and is not uploaded as gameplay dumps.

Published evaluation lives only under `benchmarks/`.
