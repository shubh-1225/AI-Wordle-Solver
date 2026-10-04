"""Structured ranking results from the entropy solver."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GuessScore:
    guess: str
    entropy: float
    feedback_groups: int
    in_candidate_set: bool
    expected_remaining: float


@dataclass(frozen=True)
class Recommendation:
    best_guess: str
    entropy: float
    feedback_groups: int
    remaining_candidates: int
    expected_remaining: float
    expected_reduction: float
    ranked_guesses: tuple[GuessScore, ...]
