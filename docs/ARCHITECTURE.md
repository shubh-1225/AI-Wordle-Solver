# Architecture

## Purpose

The application is split so that **search and information-theoretic ranking never live in the GUI**, and the GUI never reimplements Wordle coloring. That keeps the solver testable without a window and keeps the desktop app from drifting away from the same engine used in benchmarks.

## Layers

```
┌─────────────────────────────────────────────────────────────┐
│ CustomTkinter (app/gui)                                     │
│  MainWindow, WordleBoard, OnScreenKeyboard, SolverPanel,    │
│  StatisticsPanel, SimulationModePanel                       │
└──────────────────────────────┬──────────────────────────────┘
                               │ callbacks only
┌──────────────────────────────▼──────────────────────────────┐
│ GameSession (app/session.py)                                │
│  board state, keyboard colors, history, worker-thread queue │
└──────────────────────────────┬──────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
 FeedbackEngine        CandidateFilter          WordleSolver
 app/solver/           app/solver/              ranking + entropy
 feedback.py           candidates.py            + optional cache
        │                      │                      │
        └──────────────────────┴──────────────────────┘
                               ▼
                     WordleSimulator
                     simulate() / benchmark()
```

## Major modules

| Module | Role |
| --- | --- |
| `app/solver/feedback.py` | Official two-pass green-then-yellow coloring |
| `app/solver/constraints.py` | Pattern validation and contradictory-history checks |
| `app/solver/candidates.py` | Remaining-answer filter: `feedback(g, a) == observed` |
| `app/solver/entropy.py` | Partitions, Shannon entropy, expected remaining size |
| `app/solver/ranking.py` | Score and sort the guess pool |
| `app/solver/cache.py` | Base-3 pattern codes 0–242 and the NumPy matrix |
| `app/solver/solver.py` | Session-facing solver: update candidates, recommend |
| `app/solver/simulator.py` | Autonomous play and opener ranking |
| `app/session.py` | Maps GUI actions onto the solver |
| `app/models/` | Feedback constants, `GuessScore`, `Recommendation`, stats dataclasses |
| `app/gui/` | Presentation only |
| `app/utils/word_utils.py` | Load and validate `data/*.txt` |
| `app/utils/config.py` | Paths and `MAX_GUESSES = 6` |

## Data flow (assisted game)

1. The user commits a five-letter guess. `GameSession` stores letters on the current row.
2. The user colors tiles. `submit_feedback` sends `(guess, pattern)` to `WordleSolver.update`.
3. `CandidateFilter` retains answers that reproduce that pattern.
4. A background thread calls `WordleSolver.get_recommendation()`.
5. Ranking pulls a submatrix from the cache when fingerprints match; otherwise it calls `get_feedback`.
6. The UI shows the best guess, metrics, alternatives, remaining words, and compact game statistics.

## Simulation architecture

`simulate(answer, strategy, starting_word=...)` resets the solver, then for up to six turns:

1. Choose a guess (`starting_word` on turn 1, otherwise `choose_guess`).
2. Color it with `get_feedback(guess, answer)`.
3. Record entropy / groups when ranking is available.
4. Apply the observation and continue until solved or exhausted.

`WordleSimulator.benchmark_opener` plays that loop against every answer, grouping answers that share the same feedback history so equivalent remaining sets are not re-ranked. That is equivalent to one `simulate()` per answer and is how `scripts/find_best_openers.py` finishes in minutes rather than hours.

Strategies (`STRATEGIES`):

- `maximum_entropy` → rank by Shannon entropy
- `candidate_reduction` → rank by expected remaining candidate count

## Threading

Entropy ranking of ~13k guesses is too slow for the Tk main loop. `MainWindow` runs recommendation, solver-mode, and batch simulation on daemon threads and posts UI updates through a queue pumped with `after()`.

## What is intentionally not in the solver

GUI layout, tile animation, keyboard coloring heuristics, and CustomTkinter widgets. Keyboard GREEN > YELLOW > GRAY is a display rule in the session/GUI models, not part of ranking.
