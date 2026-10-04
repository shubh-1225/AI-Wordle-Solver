"""Tests for candidate filtering from guess/feedback history."""

from __future__ import annotations

import pytest

from app.models.feedback import GRAY, GREEN, YELLOW
from app.solver.candidates import CandidateFilter, filter_candidates
from app.solver.constraints import ContradictoryFeedbackError, ConstraintError
from app.solver.feedback import get_feedback
from app.utils.word_utils import load_word_data

ALL_GREEN = (GREEN, GREEN, GREEN, GREEN, GREEN)
ALL_GRAY = (GRAY, GRAY, GRAY, GRAY, GRAY)

MINI_ANSWERS = (
    "crane",
    "crate",
    "trace",
    "slate",
    "arise",
    "raise",
    "house",
    "mouse",
    "apple",
    "pleas",
    "geese",
    "great",
    "sassy",
    "guess",
    "audio",
    "comic",
    "balmy",
    "blitz",
)


def test_basic_filter_keeps_only_matching_feedback() -> None:
    remaining = filter_candidates(
        MINI_ANSWERS,
        [("house", get_feedback("house", "mouse"))],
    )
    assert remaining == ("mouse",)


def test_green_constraint_locks_position() -> None:
    remaining = filter_candidates(
        MINI_ANSWERS,
        [("crane", (GREEN, GRAY, GRAY, GRAY, GRAY))],
    )
    assert remaining == ("comic",)


def test_yellow_constraint_requires_letter_elsewhere() -> None:
    remaining = filter_candidates(
        MINI_ANSWERS,
        [("arise", (YELLOW, GRAY, GRAY, GRAY, GRAY))],
    )
    assert remaining == ("balmy",)
    assert all("a" in word and word[0] != "a" for word in remaining)


def test_gray_constraint_excludes_absent_letters() -> None:
    remaining = filter_candidates(
        MINI_ANSWERS,
        [("house", ALL_GRAY)],
    )
    assert remaining
    assert "blitz" in remaining
    for word in remaining:
        assert set(word).isdisjoint(set("house"))


def test_duplicate_letters_geese_vs_great() -> None:
    remaining = filter_candidates(
        MINI_ANSWERS,
        [("geese", get_feedback("geese", "great"))],
    )
    assert "great" in remaining
    assert "geese" not in remaining


def test_duplicate_letters_apple_second_p_gray() -> None:
    remaining = filter_candidates(
        MINI_ANSWERS,
        [("apple", get_feedback("apple", "pleas"))],
    )
    assert remaining == ("pleas",)


def test_multiple_previous_guesses_narrow_the_set() -> None:
    history = [
        ("slate", get_feedback("slate", "crane")),
        ("trace", get_feedback("trace", "crane")),
    ]
    remaining = filter_candidates(MINI_ANSWERS, history)
    assert remaining == ("crane",)


def test_incremental_filter_matches_full_history() -> None:
    engine = CandidateFilter(MINI_ANSWERS)
    engine.apply("slate", get_feedback("slate", "crane"))
    engine.apply("trace", get_feedback("trace", "crane"))
    assert engine.candidates == filter_candidates(
        MINI_ANSWERS,
        [
            ("slate", get_feedback("slate", "crane")),
            ("trace", get_feedback("trace", "crane")),
        ],
    )


def test_contradictory_feedback_same_guess_different_colors() -> None:
    with pytest.raises(ContradictoryFeedbackError, match="contradictory"):
        filter_candidates(
            MINI_ANSWERS,
            [
                ("crane", ALL_GREEN),
                ("crane", ALL_GRAY),
            ],
        )


def test_contradictory_apply_on_existing_history() -> None:
    engine = CandidateFilter(MINI_ANSWERS)
    engine.apply("crane", ALL_GREEN)
    with pytest.raises(ContradictoryFeedbackError):
        engine.apply("crane", ALL_GRAY)
    assert engine.candidates == ("crane",)


def test_zero_candidates_for_consistent_but_impossible_history() -> None:
    remaining = filter_candidates(
        MINI_ANSWERS,
        [
            ("house", ALL_GREEN),
            ("mouse", ALL_GREEN),
        ],
    )
    assert remaining == ()


def test_one_remaining_candidate_all_green() -> None:
    remaining = filter_candidates(MINI_ANSWERS, [("audio", ALL_GREEN)])
    assert remaining == ("audio",)


def test_reset_restores_full_dictionary() -> None:
    engine = CandidateFilter(MINI_ANSWERS)
    engine.apply("audio", ALL_GREEN)
    assert engine.candidates == ("audio",)
    assert engine.reset() == MINI_ANSWERS


def test_invalid_feedback_pattern_rejected() -> None:
    with pytest.raises(ConstraintError):
        filter_candidates(MINI_ANSWERS, [("crane", (GREEN, GREEN))])
    with pytest.raises(ConstraintError):
        filter_candidates(MINI_ANSWERS, [("crane", (3, 0, 0, 0, 0))])


def test_full_dictionary_unfiltered_count() -> None:
    answers = load_word_data().answers
    remaining = filter_candidates(answers, [])
    assert remaining == answers
    assert len(remaining) == 2315


def test_full_dictionary_known_states_have_stable_counts() -> None:
    answers = load_word_data().answers
    crane_all_gray = filter_candidates(answers, [("crane", ALL_GRAY)])
    crane_solved = filter_candidates(answers, [("crane", ALL_GREEN)])
    weary_vs_crane = filter_candidates(
        answers,
        [("weary", get_feedback("weary", "crane"))],
    )
    two_guesses = filter_candidates(
        answers,
        [
            ("slate", get_feedback("slate", "crane")),
            ("cramp", get_feedback("cramp", "crane")),
        ],
    )

    assert len(crane_all_gray) == 263
    assert crane_solved == ("crane",)
    assert len(weary_vs_crane) == 20
    assert two_guesses == ("crane", "crave", "craze")
    assert "crane" in weary_vs_crane
