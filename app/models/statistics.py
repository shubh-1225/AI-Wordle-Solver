"""Simulation and benchmark statistics."""

from __future__ import annotations

from dataclasses import dataclass

from app.models.feedback import FeedbackPattern


@dataclass(frozen=True)
class TurnRecord:
    guess: str
    feedback: FeedbackPattern
    candidates_after: int
    entropy: float | None
    feedback_groups: int | None


@dataclass(frozen=True)
class SimulationResult:
    answer: str
    solved: bool
    guesses: int
    guess_history: tuple[str, ...]
    feedback_history: tuple[FeedbackPattern, ...]
    candidate_counts: tuple[int, ...]
    entropies: tuple[float | None, ...]
    starting_word: str | None
    strategy: str
    turns: tuple[TurnRecord, ...]


@dataclass(frozen=True)
class BenchmarkSummary:
    strategy: str
    starting_word: str | None
    games: int
    wins: int
    failures: int
    win_rate: float
    average_guesses: float
    median_guesses: float
    minimum_guesses: int
    maximum_guesses: int
    average_guesses_including_failures: float
    guess_distribution: dict[int, int]
    failed: int
    results: tuple[SimulationResult, ...]


@dataclass(frozen=True)
class OpenerReport:
    opener: str
    in_answer_list: bool
    first_guess_entropy: float
    games: int
    wins: int
    failures: int
    win_rate: float
    average_guesses: float
    median_guesses: float
    minimum_guesses: int
    maximum_guesses: int
    average_guesses_including_failures: float
    guess_distribution: dict[int, int]
    worst_case_answers: tuple[str, ...]
    failed_answers: tuple[str, ...]
    elapsed_seconds: float
