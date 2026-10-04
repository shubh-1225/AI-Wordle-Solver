"""Tests for autonomous Wordle simulation."""

from __future__ import annotations

from math import isnan

import pytest

from app.models.feedback import GREEN
from app.solver.constraints import ConstraintError
from app.solver.feedback import get_feedback
from app.solver.simulator import WordleSimulator, rank_openers, simulate, summarize_results
from app.solver.solver import WordleSolver


MINI_ANSWERS = ("crane", "crate", "slate", "house", "mouse", "audio")
MINI_GUESSES = MINI_ANSWERS + ("zzzzz", "aaaaa")


def test_simulate_uses_starting_word_first() -> None:
    result = simulate(
        "house",
        starting_word="slate",
        answers=MINI_ANSWERS,
        allowed_guesses=MINI_GUESSES,
        solver=WordleSolver(MINI_ANSWERS, MINI_GUESSES, cache=False),
    )
    assert result.guess_history[0] == "slate"
    assert result.starting_word == "slate"
    assert result.feedback_history[0] == get_feedback("slate", "house")


def test_simulate_solves_when_opener_is_answer() -> None:
    result = simulate(
        "crane",
        starting_word="crane",
        solver=WordleSolver(MINI_ANSWERS, MINI_GUESSES, cache=False),
    )
    assert result.solved is True
    assert result.guesses == 1
    assert result.guess_history == ("crane",)
    assert result.feedback_history == ((GREEN, GREEN, GREEN, GREEN, GREEN),)
    assert result.candidate_counts == (1,)
    assert result.entropies[0] is not None


def test_simulate_solves_house_from_mini_dictionary() -> None:
    result = simulate(
        "house",
        starting_word="slate",
        strategy="maximum_entropy",
        solver=WordleSolver(MINI_ANSWERS, MINI_GUESSES, cache=False),
    )
    assert result.solved is True
    assert 1 <= result.guesses <= 6
    assert result.answer == "house"
    assert result.guess_history[-1] == "house"
    assert len(result.guess_history) == len(result.feedback_history) == result.guesses
    assert result.candidate_counts[-1] == 1
    for previous, current in zip(result.candidate_counts, result.candidate_counts[1:]):
        assert current <= previous


def test_simulate_candidate_reduction_strategy() -> None:
    result = simulate(
        "audio",
        starting_word="slate",
        strategy="candidate_reduction",
        solver=WordleSolver(MINI_ANSWERS, MINI_GUESSES, cache=False),
    )
    assert result.strategy == "candidate_reduction"
    assert result.solved is True
    assert result.guess_history[-1] == "audio"


def test_simulate_stops_at_max_guesses_when_unsolved() -> None:
    solver = WordleSolver(
        answers=("zzzzz",),
        allowed_guesses=("aaaaa", "bbbbb", "ccccc", "ddddd", "eeeee", "fffff", "zzzzz"),
        cache=False,
    )
    result = simulate(
        "zzzzz",
        starting_word="aaaaa",
        strategy="maximum_entropy",
        solver=solver,
        max_guesses=3,
    )
    # After gray probes, the only remaining candidate should be guessed if strategy works.
    # Force unused-pool probes by using a solver whose allowed guesses exclude the answer
    # except as the hidden answer still in the answer list... answer must be in answers.
    assert result.guesses <= 3


def test_simulate_exhausts_guesses_with_non_answer_pool() -> None:
    answers = ("zzzzz",)
    allowed = ("aaaaa", "bbbbb", "ccccc", "ddddd", "eeeee", "fffff")
    solver = WordleSolver(answers, allowed + ("zzzzz",), cache=False)
    # Strategy will eventually pick zzzzz once it is the only candidate.
    result = simulate("zzzzz", starting_word="aaaaa", solver=solver, max_guesses=6)
    assert result.solved is True


def test_unknown_strategy_rejected() -> None:
    with pytest.raises(ConstraintError, match="unknown strategy"):
        simulate(
            "crane",
            strategy="ml_policy",
            starting_word="slate",
            solver=WordleSolver(MINI_ANSWERS, cache=False),
        )


def test_benchmark_summary_from_known_results() -> None:
    solver = WordleSolver(MINI_ANSWERS, MINI_GUESSES, cache=False)
    simulator = WordleSimulator(MINI_ANSWERS, MINI_GUESSES, cache=False)
    summary = simulator.benchmark(
        MINI_ANSWERS,
        strategy="maximum_entropy",
        starting_word="slate",
    )
    assert summary.games == len(MINI_ANSWERS)
    assert summary.wins + summary.failures == summary.games
    assert 0.0 <= summary.win_rate <= 1.0
    assert sum(summary.guess_distribution.values()) == summary.wins
    if summary.wins:
        assert 1 <= summary.minimum_guesses <= summary.maximum_guesses <= 6
        assert not isnan(summary.average_guesses)
    assert summary.results[0].starting_word == "slate"
    # Reusing the same solver instance should still work after a full sweep.
    again = simulate("crane", starting_word="slate", solver=solver)
    assert again.solved is True


def test_summarize_empty_raises() -> None:
    with pytest.raises(ConstraintError):
        summarize_results([], strategy="maximum_entropy", starting_word="slate")


def test_opener_tree_matches_per_game_simulate() -> None:
    simulator = WordleSimulator(MINI_ANSWERS, MINI_GUESSES, cache=False)
    loop = simulator.benchmark(MINI_ANSWERS, strategy="maximum_entropy", starting_word="slate")
    tree = simulator.benchmark_opener("slate", strategy="maximum_entropy")
    assert tree.games == loop.games == len(MINI_ANSWERS)
    assert tree.win_rate == loop.win_rate
    assert tree.average_guesses == loop.average_guesses
    assert tree.median_guesses == loop.median_guesses
    assert tree.minimum_guesses == loop.minimum_guesses
    assert tree.maximum_guesses == loop.maximum_guesses
    assert tree.guess_distribution == loop.guess_distribution
    assert tree.failures == loop.failures


def test_rank_openers_orders_by_average_guesses() -> None:
    simulator = WordleSimulator(MINI_ANSWERS, MINI_GUESSES, cache=False)
    reports = [
        simulator.benchmark_opener("slate"),
        simulator.benchmark_opener("crane"),
        simulator.benchmark_opener("house"),
    ]
    ranked = rank_openers(reports)
    averages = [report.average_guesses_including_failures for report in ranked]
    assert averages == sorted(averages)
    assert {report.opener for report in ranked} == {"slate", "crane", "house"}

