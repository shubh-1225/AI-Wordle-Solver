"""Tests for feedback-history constraint helpers."""

from __future__ import annotations

import pytest

from app.models.feedback import GRAY, GREEN, YELLOW
from app.solver.constraints import (
    ContradictoryFeedbackError,
    ConstraintError,
    detect_contradictory_history,
    normalize_observation,
    normalize_pattern,
)


def test_normalize_pattern_accepts_valid_values() -> None:
    assert normalize_pattern([0, 1, 2, 1, 0]) == (GRAY, YELLOW, GREEN, YELLOW, GRAY)


def test_normalize_observation_lowercases_guess() -> None:
    observation = normalize_observation("CRANE", (2, 2, 2, 2, 2))
    assert observation.guess == "crane"
    assert observation.feedback == (GREEN, GREEN, GREEN, GREEN, GREEN)


def test_detect_contradictory_history() -> None:
    history = (
        normalize_observation("crane", (2, 2, 2, 2, 2)),
        normalize_observation("crane", (0, 0, 0, 0, 0)),
    )
    with pytest.raises(ContradictoryFeedbackError):
        detect_contradictory_history(history)


def test_same_guess_same_feedback_is_allowed() -> None:
    history = (
        normalize_observation("crane", (1, 0, 2, 0, 0)),
        normalize_observation("crane", (1, 0, 2, 0, 0)),
    )
    detect_contradictory_history(history)


def test_invalid_pattern_value() -> None:
    with pytest.raises(ConstraintError, match="0, 1, or 2"):
        normalize_pattern((0, 0, 0, 0, 9))
