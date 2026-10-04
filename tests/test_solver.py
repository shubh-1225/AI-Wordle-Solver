"""Tests for guess ranking and the entropy WordleSolver."""

from __future__ import annotations

import pytest

from app.models.feedback import GREEN
from app.solver.constraints import ConstraintError
from app.solver.entropy import calculate_entropy
from app.solver.ranking import get_best_guess, rank_guesses
from app.solver.solver import WordleSolver
from app.utils.word_utils import load_word_data


def test_rank_prefers_higher_entropy() -> None:
    candidates = ["aaaaa", "bbbbb", "ccccc", "ddddd"]
    ranked = rank_guesses(["xxxxz", "abcdx"], candidates)
    assert ranked[0].guess == "abcdx"
    assert ranked[0].entropy == pytest.approx(2.0)
    assert ranked[1].guess == "xxxxz"
    assert ranked[1].entropy == pytest.approx(0.0)


def test_rank_prefers_candidate_on_entropy_tie() -> None:
    candidates = ["aaaaa"]
    ranked = rank_guesses(["bbbbb", "aaaaa"], candidates)
    assert ranked[0].entropy == ranked[1].entropy == 0.0
    assert ranked[0].guess == "aaaaa"
    assert ranked[0].in_candidate_set is True
    assert ranked[1].in_candidate_set is False


def test_probe_guess_can_outrank_a_candidate() -> None:
    candidates = ["aaaaa", "bbbbb", "ccccc", "ddddd"]
    ranked = rank_guesses(["aaaaa", "abcdx"], candidates)
    assert ranked[0].guess == "abcdx"
    assert ranked[0].in_candidate_set is False
    assert ranked[1].guess == "aaaaa"
    assert ranked[1].in_candidate_set is True
    assert ranked[0].entropy > ranked[1].entropy


def test_get_best_guess_returns_top_ranked() -> None:
    candidates = ["aaaaa", "bbbbb"]
    best = get_best_guess(["abxxx", "xxxxz"], candidates)
    assert best.guess == "abxxx"
    assert best.feedback_groups == 2


def test_score_reports_whether_guess_is_a_candidate() -> None:
    candidates = ["crane", "slate"]
    ranked = rank_guesses(["crane", "zzzzz"], candidates)
    by_guess = {score.guess: score for score in ranked}
    assert by_guess["crane"].in_candidate_set is True
    assert by_guess["zzzzz"].in_candidate_set is False


def test_solver_uses_allowed_guesses_not_only_candidates() -> None:
    solver = WordleSolver(
        answers=["aaaaa", "bbbbb", "ccccc", "ddddd"],
        allowed_guesses=["aaaaa", "abcdx"],
    )
    recommendation = solver.get_recommendation(limit=2)
    assert recommendation.best_guess == "abcdx"
    assert recommendation.remaining_candidates == 4
    assert recommendation.feedback_groups == 4
    assert recommendation.ranked_guesses[0].in_candidate_set is False
    assert recommendation.ranked_guesses[1].guess == "aaaaa"
    assert recommendation.ranked_guesses[1].in_candidate_set is True


def test_solver_update_narrows_then_recommends_remaining_word() -> None:
    solver = WordleSolver(
        answers=["crane", "slate", "audio"],
        allowed_guesses=["crane", "slate", "audio", "zzzzz"],
    )
    solver.update("audio", (GREEN, GREEN, GREEN, GREEN, GREEN))
    assert solver.get_candidates() == ("audio",)
    best = solver.get_best_guess()
    assert best.guess == "audio"
    assert best.in_candidate_set is True
    assert best.entropy == 0.0


def test_solver_get_entropy_matches_module() -> None:
    solver = WordleSolver(answers=["aaaaa", "bbbbb"], allowed_guesses=["abxxx"])
    assert solver.get_entropy("abxxx") == pytest.approx(
        calculate_entropy("abxxx", ["aaaaa", "bbbbb"])
    )


def test_rank_empty_inputs_raise() -> None:
    with pytest.raises(ConstraintError):
        rank_guesses(["crane"], [])
    with pytest.raises(ConstraintError):
        rank_guesses([], ["crane"])


def test_full_dictionary_opener_entropies_are_ordered() -> None:
    answers = load_word_data().answers
    crane = calculate_entropy("crane", answers)
    xylyl = calculate_entropy("xylyl", answers)
    assert crane > xylyl
    assert 5.0 < crane < 6.5
    assert xylyl < 4.5
