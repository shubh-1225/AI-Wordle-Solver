"""Autonomous Wordle simulation and benchmarking."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from statistics import mean, median
from time import perf_counter

from app.models.recommendation import GuessScore
from app.models.statistics import BenchmarkSummary, OpenerReport, SimulationResult, TurnRecord
from app.solver.constraints import ConstraintError
from app.solver.entropy import calculate_entropy, partition_candidates
from app.solver.feedback import get_feedback, normalize_word
from app.solver.ranking import rank_guesses, score_guess
from app.solver.solver import WordleSolver
from app.utils.config import MAX_GUESSES

STRATEGIES = ("maximum_entropy", "candidate_reduction")


def _ranking_objective(strategy: str) -> str:
    if strategy == "maximum_entropy":
        return "entropy"
    if strategy == "candidate_reduction":
        return "expected_remaining"
    raise ConstraintError(
        f"unknown strategy {strategy!r}; expected one of {STRATEGIES}"
    )


def choose_guess(
    candidates: Sequence[str],
    allowed_guesses: Sequence[str],
    *,
    strategy: str = "maximum_entropy",
    used_guesses: Sequence[str] = (),
    cache: object = None,
) -> GuessScore:
    """Choose the next guess from remaining candidates / allowed pool."""
    if not candidates:
        raise ConstraintError("no remaining candidates to guess")
    if len(candidates) == 1:
        return score_guess(candidates[0], candidates, cache=cache)

    used = set(used_guesses)
    pool = [word for word in allowed_guesses if word not in used]
    if not pool:
        pool = [word for word in candidates if word not in used]
    if not pool:
        raise ConstraintError("no unused guesses remain")
    return rank_guesses(
        pool,
        candidates,
        limit=1,
        cache=cache,
        objective=_ranking_objective(strategy),
    )[0]


def select_next_guess(
    solver: WordleSolver,
    *,
    strategy: str = "maximum_entropy",
    used_guesses: Sequence[str] = (),
) -> GuessScore:
    return choose_guess(
        solver.get_candidates(),
        solver.allowed_guesses,
        strategy=strategy,
        used_guesses=used_guesses,
        cache=solver.pattern_cache,
    )


def simulate(
    answer: str,
    strategy: str = "maximum_entropy",
    *,
    starting_word: str | None = None,
    solver: WordleSolver | None = None,
    answers: Sequence[str] | None = None,
    allowed_guesses: Sequence[str] | None = None,
    max_guesses: int = MAX_GUESSES,
) -> SimulationResult:
    """Play one autonomous game against a hidden answer."""
    if strategy not in STRATEGIES:
        raise ConstraintError(
            f"unknown strategy {strategy!r}; expected one of {STRATEGIES}"
        )
    answer_word = normalize_word(answer, label="answer")
    opener = (
        normalize_word(starting_word, label="starting_word")
        if starting_word is not None
        else None
    )
    if solver is None:
        if answers is None:
            raise ConstraintError("simulate() requires a solver or an answer list")
        solver = WordleSolver(answers, allowed_guesses)
    solver.reset()

    if answer_word not in solver.answers:
        raise ConstraintError(f"answer {answer_word!r} is not in the answer dictionary")
    if opener is not None and opener not in solver.allowed_guesses:
        raise ConstraintError(
            f"starting word {opener!r} is not in the allowed guess list"
        )

    turns: list[TurnRecord] = []
    used: list[str] = []

    for turn_index in range(max_guesses):
        if turn_index == 0 and opener is not None:
            guess = opener
            try:
                entropy = solver.get_entropy(guess)
                groups: int | None = None
            except ConstraintError:
                entropy = None
                groups = None
        else:
            scored = select_next_guess(solver, strategy=strategy, used_guesses=used)
            guess = scored.guess
            entropy = scored.entropy
            groups = scored.feedback_groups

        feedback = get_feedback(guess, answer_word)
        solver.update(guess, feedback)
        used.append(guess)
        turns.append(
            TurnRecord(
                guess=guess,
                feedback=feedback,
                candidates_after=len(solver.get_candidates()),
                entropy=entropy,
                feedback_groups=groups,
            )
        )
        if guess == answer_word:
            break

    solved = bool(turns) and turns[-1].guess == answer_word
    return SimulationResult(
        answer=answer_word,
        solved=solved,
        guesses=len(turns),
        guess_history=tuple(turn.guess for turn in turns),
        feedback_history=tuple(turn.feedback for turn in turns),
        candidate_counts=tuple(turn.candidates_after for turn in turns),
        entropies=tuple(turn.entropy for turn in turns),
        starting_word=opener,
        strategy=strategy,
        turns=tuple(turns),
    )


def summarize_results(
    results: Sequence[SimulationResult],
    *,
    strategy: str,
    starting_word: str | None,
    max_guesses: int = MAX_GUESSES,
) -> BenchmarkSummary:
    if not results:
        raise ConstraintError("cannot summarize an empty simulation set")

    solved_guesses = [result.guesses for result in results if result.solved]
    wins = len(solved_guesses)
    failures = len(results) - wins
    distribution: dict[int, int] = {turn: 0 for turn in range(1, max_guesses + 1)}
    for result in results:
        if result.solved:
            distribution[result.guesses] += 1

    including_failures = [
        result.guesses if result.solved else max_guesses + 1 for result in results
    ]
    return BenchmarkSummary(
        strategy=strategy,
        starting_word=starting_word,
        games=len(results),
        wins=wins,
        failures=failures,
        win_rate=wins / len(results),
        average_guesses=mean(solved_guesses) if solved_guesses else float("nan"),
        median_guesses=float(median(solved_guesses)) if solved_guesses else float("nan"),
        minimum_guesses=min(solved_guesses) if solved_guesses else 0,
        maximum_guesses=max(solved_guesses) if solved_guesses else 0,
        average_guesses_including_failures=mean(including_failures),
        guess_distribution=distribution,
        failed=failures,
        results=tuple(results),
    )


def _counts_from_outcomes(
    outcomes: dict[str, tuple[int, bool]],
    *,
    max_guesses: int,
) -> tuple[list[int], dict[int, int], list[str], list[str]]:
    solved_guesses: list[int] = []
    distribution = {turn: 0 for turn in range(1, max_guesses + 1)}
    failed_answers: list[str] = []
    for answer, (guesses, solved) in outcomes.items():
        if solved:
            solved_guesses.append(guesses)
            distribution[guesses] += 1
        else:
            failed_answers.append(answer)
    worst = max((guesses for guesses, solved in outcomes.values() if solved), default=0)
    worst_answers = [
        answer for answer, (guesses, solved) in outcomes.items() if solved and guesses == worst
    ]
    return solved_guesses, distribution, failed_answers, worst_answers


def benchmark_opener(
    starting_word: str,
    solver: WordleSolver,
    *,
    strategy: str = "maximum_entropy",
    max_guesses: int = MAX_GUESSES,
) -> OpenerReport:
    """Simulate every answer after a fixed first guess.

    Answers that share the same feedback history are processed together, which
    is equivalent to calling simulate() once per answer for a deterministic
    strategy.
    """
    if strategy not in STRATEGIES:
        raise ConstraintError(
            f"unknown strategy {strategy!r}; expected one of {STRATEGIES}"
        )
    opener = normalize_word(starting_word, label="starting_word")
    if opener not in solver.allowed_guesses:
        raise ConstraintError(
            f"starting word {opener!r} is not in the allowed guess list"
        )

    started = perf_counter()
    answers = solver.answers
    cache = solver.pattern_cache
    first_guess_entropy = calculate_entropy(opener, answers, cache=cache)
    outcomes: dict[str, tuple[int, bool]] = {}

    def walk(candidates: Sequence[str], used: tuple[str, ...], depth: int) -> None:
        if not candidates:
            return
        if depth == 0:
            guess = opener
        else:
            guess = choose_guess(
                candidates,
                solver.allowed_guesses,
                strategy=strategy,
                used_guesses=used,
                cache=cache,
            ).guess

        groups = partition_candidates(guess, candidates, cache=cache)
        next_used = (*used, guess)
        guesses_used = depth + 1
        for group in groups.values():
            remaining = [word for word in group if word != guess]
            if guess in group:
                outcomes[guess] = (guesses_used, True)
            if not remaining:
                continue
            if guesses_used >= max_guesses:
                for word in remaining:
                    outcomes[word] = (guesses_used, False)
            else:
                walk(remaining, next_used, guesses_used)

    walk(answers, (), 0)
    if len(outcomes) != len(answers):
        missing = [word for word in answers if word not in outcomes]
        raise ConstraintError(
            f"opener benchmark missed {len(missing)} answer(s), including {missing[:5]!r}"
        )

    solved_guesses, distribution, failed_answers, worst_answers = _counts_from_outcomes(
        outcomes, max_guesses=max_guesses
    )
    wins = len(solved_guesses)
    failures = len(failed_answers)
    including_failures = [
        guesses if solved else max_guesses + 1 for guesses, solved in outcomes.values()
    ]
    return OpenerReport(
        opener=opener,
        in_answer_list=opener in set(answers),
        first_guess_entropy=first_guess_entropy,
        games=len(answers),
        wins=wins,
        failures=failures,
        win_rate=wins / len(answers),
        average_guesses=mean(solved_guesses) if solved_guesses else float("nan"),
        median_guesses=float(median(solved_guesses)) if solved_guesses else float("nan"),
        minimum_guesses=min(solved_guesses) if solved_guesses else 0,
        maximum_guesses=max(solved_guesses) if solved_guesses else 0,
        average_guesses_including_failures=mean(including_failures),
        guess_distribution=distribution,
        worst_case_answers=tuple(sorted(worst_answers)),
        failed_answers=tuple(sorted(failed_answers)),
        elapsed_seconds=perf_counter() - started,
    )


def rank_openers(reports: Sequence[OpenerReport]) -> tuple[OpenerReport, ...]:
    """Rank openers on this dictionary/solver only. Lower average is better."""
    return tuple(
        sorted(
            reports,
            key=lambda report: (
                report.average_guesses_including_failures,
                report.average_guesses,
                -report.win_rate,
                report.maximum_guesses,
                report.opener,
            ),
        )
    )


class WordleSimulator:
    """Run autonomous games and aggregate solver performance."""

    def __init__(
        self,
        answers: Sequence[str],
        allowed_guesses: Sequence[str] | None = None,
        *,
        cache: object = True,
        max_guesses: int = MAX_GUESSES,
    ) -> None:
        self.solver = WordleSolver(answers, allowed_guesses, cache=cache)  # type: ignore[arg-type]
        self.max_guesses = max_guesses

    def simulate(
        self,
        answer: str,
        strategy: str = "maximum_entropy",
        *,
        starting_word: str | None = None,
    ) -> SimulationResult:
        return simulate(
            answer,
            strategy,
            starting_word=starting_word,
            solver=self.solver,
            max_guesses=self.max_guesses,
        )

    def benchmark(
        self,
        answers: Sequence[str] | None = None,
        *,
        strategy: str = "maximum_entropy",
        starting_word: str | None = None,
        progress: Callable[[int, int, SimulationResult], None] | None = None,
    ) -> BenchmarkSummary:
        target = tuple(answers) if answers is not None else self.solver.answers
        results: list[SimulationResult] = []
        total = len(target)
        for index, answer in enumerate(target, start=1):
            result = self.simulate(answer, strategy, starting_word=starting_word)
            results.append(result)
            if progress is not None:
                progress(index, total, result)
        return summarize_results(
            results,
            strategy=strategy,
            starting_word=starting_word,
            max_guesses=self.max_guesses,
        )

    def benchmark_opener(
        self,
        starting_word: str,
        *,
        strategy: str = "maximum_entropy",
    ) -> OpenerReport:
        return benchmark_opener(
            starting_word,
            self.solver,
            strategy=strategy,
            max_guesses=self.max_guesses,
        )
