# AI Wordle Solver

A standalone **Python desktop** Wordle solver that combines **constraint satisfaction** with **information theory**. It recommends guesses that maximize expected information gain (Shannon entropy) over the remaining answer set. An autonomous simulator evaluates that policy on the complete original Wordle answer list.

This is **not** an LLM chatbot. Guesses come from an explicit feedback engine, a candidate filter, and entropy-based ranking over a fixed dictionary.

## Overview

Wordle is a six-turn search problem: each guess produces a five-cell green / yellow / gray pattern that constrains the hidden answer. This project treats that pattern as a **partition of the candidate space** and scores every allowed guess by how evenly it splits remaining answers.

```
Wordle feedback
        ↓
Constraint satisfaction / candidate filtering
        ↓
Feedback partitions of the remaining answers
        ↓
Shannon entropy H(g) = -Σ pᵢ log₂(pᵢ)
        ↓
Ranked next guess (greedy information gain)
```

A CustomTkinter GUI lets a human play with AI assistance. Solver mode plays a hidden answer autonomously. Simulation mode batches games in the background.

## Features

- Interactive 5×6 Wordle board, QWERTY keyboard, and tile-color feedback
- Constraint-based candidate filtering (a word remains only if it reproduces every observed pattern)
- Entropy-based guess ranking over the allowed-guess vocabulary
- Candidate count, entropy, feedback-group count, and expected candidate reduction
- Two greedy strategies: **maximum entropy** and **minimum expected remaining candidates**
- Precomputed `uint8` feedback matrix (optional, ~29 MiB, generated locally)
- Autonomous single-game solver and full-dictionary opener benchmarking
- In-session game statistics (guess number, remaining candidates, cumulative information, status)
- Pytest coverage for feedback (including duplicate letters), filtering, entropy, cache, simulation, and GUI smoke tests

Not implemented: neural nets, reinforcement learning, multi-ply lookahead / expected remaining-guess search, or a live New York Times vocabulary client.

## AI Methodology

### 1. Wordle feedback

Each cell is `0` gray, `1` yellow, or `2` green. Greens are assigned first; leftover answer letters are then used for yellows. That two-pass rule is required for duplicate letters (`sassy`, `alloy`, and similar cases).

### 2. Constraint satisfaction

After each observation `(guess, pattern)`, the hidden answer must lie in the set of dictionary answers that would have produced **exactly** that pattern. The solver does not maintain a separate algebraic constraint store; the candidate set **is** the CSP state.

### 3. Candidate filtering

```text
C₀ = answers
Cₜ₊₁ = { a ∈ Cₜ | feedback(gₜ, a) = observed patternₜ }
```

Contradictory history (the same guess scored two different ways) is rejected.

### 4. Information theory

A guess `g` maps each remaining answer to one of 243 = 3⁵ possible patterns. If pattern `i` occurs for `nᵢ` of `N` candidates, then `pᵢ = nᵢ / N` and

```text
H(g) = - Σᵢ pᵢ log₂(pᵢ)
```

`H(g)` is the expected information in bits. The solver also records the number of nonempty pattern groups and the expected remaining size `Σᵢ nᵢ² / N`.

### 5. Guess ranking

Allowed guesses (including non-answer probes) are scored. Ranking key:

1. higher entropy (or, for `candidate_reduction`, lower expected remaining)
2. prefer a word that is still a possible answer
3. alphabetical tie-break

When one candidate remains, the solver names that word.

### 6. Optimization

The published policy is **greedy one-ply** ranking with an optional precomputed feedback matrix. There is **no** multi-step lookahead or expected-remaining-guesses search in this release.

## Architecture

```
User
  ↓
CustomTkinter GUI (board, keyboard, panels)
  ↓
GameSession          ← no entropy math in the GUI
  ↓
FeedbackEngine  →  CandidateFilter  →  WordleSolver
  ↓                     ↓                    ↓
get_feedback()     remaining answers     rank_guesses()
  ↓                                          ↓
optional FeedbackPatternCache (NumPy uint8)
  ↓
Recommendation / SimulationResult / BenchmarkSummary
```

`app/solver/` never imports the GUI. The GUI never computes entropy.

## Technology stack

- Python 3.11+
- CustomTkinter
- NumPy
- Pytest

## Installation

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
```

macOS / Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

Optional speed-up (once per machine; writes `cache/feedback_patterns.npz`, not committed):

```bash
python scripts/precompute_patterns.py
```

Run the desktop app:

```bash
python main.py
```

## How to use

**Assist mode**

1. Type a five-letter guess (keyboard or on-screen keys) and press Enter.
2. Click tiles to cycle gray → yellow → green to match the real Wordle coloring.
3. Submit feedback.
4. Read the AI recommendation, metrics, remaining candidates, and game statistics.
5. Repeat until the answer is green or six guesses are used.

**Solver mode** plays a hidden answer (typed or random) with a chosen strategy and opener. Turns appear on the board.

**Simulation mode** runs a background batch (default opener `soare`) and writes aggregate win-rate / guess statistics into the Game Statistics panel. Those session stats are separate from the published full-dictionary benchmarks in `benchmarks/results/`.

## Example

Hidden answer `crane`, first guess `soare`, maximum-entropy ranking, original 2,315 / 12,972 lists, cache enabled.

| Step | Value |
| --- | --- |
| Opening recommendation | `soare` |
| Opening entropy | 5.886 bits |
| Feedback groups / expected remaining | 127 groups, 62.3 answers, 97.3% expected reduction |
| Feedback for `soare` vs `crane` | gray, gray, green, yellow, green |
| Candidates remaining | 19 |
| Next recommendation | `diact` (2.971 bits, 10 groups) |

## Benchmark results

Full-game evaluation of the five highest first-guess-entropy openers against **all 2,315 answers**, later guesses by **maximum entropy**. Failures would count as 7 guesses; there were none.

| Rank | Opener | In answers? | H₁ (bits) | Avg guesses | Median | Worst | Win rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | reast | no | 5.865 | 3.437 | 3 | 5 | 100% |
| 2 | soare | no | 5.886 | 3.465 | 3 | 6 | 100% |
| 3 | roate | no | 5.883 | 3.467 | 3 | 5 | 100% |
| 4 | raile | no | 5.866 | 3.469 | 3 | 5 | 100% |
| 5 | raise | yes | 5.878 | 3.472 | 3 | 6 | 100% |

`soare` guess distribution: 44 / 1,216 / 991 / 63 / 1 games in 2–6 guesses.

Highest first-guess entropy (`soare`) was **not** the lowest full-game average (`reast`). Greedy information on turn 1 is not the same as expected remaining guesses over a whole game.

The `candidate_reduction` strategy is implemented and selectable, but this repository does **not** publish a full 2,315-answer sweep for it.

Details: [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md), [`docs/EXPERIMENTS.md`](docs/EXPERIMENTS.md), [`benchmarks/results/`](benchmarks/results/).

## Research / engineering findings

- The candidate set collapses quickly: `soare` has 127 opening partitions and an expected remaining size of about 62 of 2,315.
- On this dictionary, several high-entropy openers all win 100% of games with averages between 3.44 and 3.47.
- Non-answer openers (`reast`, `soare`, `roate`, `raile`) beat the answer-word opener `raise` on average guesses.
- A 12,972 × 2,315 `uint8` matrix makes full-dictionary ranking and simulation practical (about 93 seconds per opener on the machine that produced the published JSON).
- One-ply entropy is a strong but not theoretically optimal policy.

## Limitations

- Results apply only to the original Wordle lists in `data/`, not the live NYT list.
- The solver is greedy; it does not prove minimax or expected-guess optimality.
- Hard mode is not implemented.
- Duplicate-letter edge cases are tested, but any mismatch with a future official coloring change would affect the whole pipeline.
- The precomputed cache is large and machine-local.
- In-app simulation of a few games is not a substitute for the published 2,315-answer runs.

## Future work

- Multi-ply lookahead / expected remaining guesses
- Learned policies (supervised or RL) on top of the same feedback engine
- Live vocabulary updates
- A published `candidate_reduction` full sweep
- Richer visualizations inside the GUI

## Testing

```bash
pytest
```

Covered areas include duplicate-letter feedback, candidate filtering, entropy partitions, solver recommendations, the pattern cache, autonomous simulation, the session layer, and a headless GUI smoke test.

## Reproducing benchmarks

```bash
python scripts/precompute_patterns.py
python scripts/find_best_openers.py --top-entropy 5 --strategy maximum_entropy
python scripts/export_benchmark_artifacts.py
```

Single-opener sweep:

```bash
python scripts/benchmark_solver.py --opener soare --strategy maximum_entropy
```

The ranking is deterministic given the word lists, strategy, and opener. No random seed is required for those published runs.

## Project structure

```text
AI-Wordle-Solver/
├── README.md
├── LICENSE
├── requirements.txt
├── pyproject.toml
├── main.py
├── app/                 # GUI, session, solver, models
├── data/                # answer and allowed-guess lists
├── scripts/             # cache, benchmarks, figure export
├── tests/
├── benchmarks/          # results, figures, regeneration notes
├── docs/                # architecture, algorithms, experiments
└── cache/               # generated locally, not committed
```

## Author

Shubh

## License

Source code is MIT. Word lists in `data/` are third-party extracts documented in [`docs/DATASET.md`](docs/DATASET.md).
