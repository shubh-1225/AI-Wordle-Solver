"""Filter remaining answer candidates from guess/feedback history.

Correctness-first: a candidate remains only if
`get_feedback(guess, candidate) == observed_feedback`
for every previous guess. Duplicate-letter coloring is therefore identical
to the feedback engine.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from app.models.feedback import FeedbackPattern
from app.models.game import GuessObservation
from app.solver.constraints import (
    ConstraintError,
    detect_contradictory_history,
    normalize_observation,
)
from app.solver.feedback import get_feedback


class CandidateFilter:
    """Maintain the remaining answer set after each observation."""

    def __init__(self, answers: Sequence[str]) -> None:
        if not answers:
            raise ConstraintError("answer dictionary must not be empty")
        self._answers = tuple(answers)
        self._history: list[GuessObservation] = []
        self._candidates = self._answers

    @property
    def answers(self) -> tuple[str, ...]:
        return self._answers

    @property
    def history(self) -> tuple[GuessObservation, ...]:
        return tuple(self._history)

    @property
    def candidates(self) -> tuple[str, ...]:
        return self._candidates

    def reset(self) -> tuple[str, ...]:
        self._history.clear()
        self._candidates = self._answers
        return self._candidates

    def apply(self, guess: str, feedback: Sequence[int]) -> tuple[str, ...]:
        observation = normalize_observation(guess, feedback)
        detect_contradictory_history((*self._history, observation))
        self._history.append(observation)
        self._candidates = _matching_candidates(self._candidates, (observation,))
        return self._candidates

    def filter_history(
        self,
        history: Sequence[tuple[str, Sequence[int]]],
    ) -> tuple[str, ...]:
        self.reset()
        for guess, feedback in history:
            self.apply(guess, feedback)
        return self._candidates


def matches_history(candidate: str, history: Sequence[GuessObservation]) -> bool:
    return all(
        get_feedback(observation.guess, candidate) == observation.feedback
        for observation in history
    )


def _matching_candidates(
    answers: Iterable[str],
    history: Sequence[GuessObservation],
) -> tuple[str, ...]:
    return tuple(word for word in answers if matches_history(word, history))


def filter_candidates(
    answers: Sequence[str],
    history: Sequence[tuple[str, Sequence[int]]],
) -> tuple[str, ...]:
    """Return answers consistent with every guess/feedback pair."""
    observations = [normalize_observation(guess, feedback) for guess, feedback in history]
    detect_contradictory_history(observations)
    return _matching_candidates(answers, observations)
