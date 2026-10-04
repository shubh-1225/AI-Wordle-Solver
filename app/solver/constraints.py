"""Guess/feedback history helpers for candidate filtering."""

from __future__ import annotations

from collections.abc import Sequence

from app.models.feedback import GRAY, GREEN, WORD_LENGTH, YELLOW, FeedbackPattern
from app.models.game import GuessObservation
from app.solver.feedback import normalize_word


class ConstraintError(ValueError):
    """Raised when feedback history cannot be applied."""


class ContradictoryFeedbackError(ConstraintError):
    """Raised when the same guess is given two different feedback patterns."""


def normalize_pattern(feedback: Sequence[int], *, label: str = "feedback") -> FeedbackPattern:
    if len(feedback) != WORD_LENGTH:
        raise ConstraintError(
            f"{label} must contain exactly {WORD_LENGTH} values, got {len(feedback)}"
        )
    values: list[int] = []
    for index, value in enumerate(feedback):
        if value not in (GRAY, YELLOW, GREEN):
            raise ConstraintError(
                f"{label}[{index}] must be 0, 1, or 2, got {value!r}"
            )
        values.append(int(value))
    return (values[0], values[1], values[2], values[3], values[4])


def normalize_observation(guess: str, feedback: Sequence[int]) -> GuessObservation:
    return GuessObservation(
        guess=normalize_word(guess, label="guess"),
        feedback=normalize_pattern(feedback),
    )


def detect_contradictory_history(
    history: Sequence[GuessObservation],
) -> None:
    seen: dict[str, FeedbackPattern] = {}
    for observation in history:
        previous = seen.get(observation.guess)
        if previous is not None and previous != observation.feedback:
            raise ContradictoryFeedbackError(
                f"Guess {observation.guess!r} has contradictory feedback: "
                f"{previous} vs {observation.feedback}"
            )
        seen[observation.guess] = observation.feedback
