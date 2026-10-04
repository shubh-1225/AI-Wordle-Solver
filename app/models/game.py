"""Assisted-play game state. No entropy or candidate-filter math lives here."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.models.feedback import GRAY, GREEN, WORD_LENGTH, YELLOW, FeedbackPattern
from app.utils.config import MAX_GUESSES

KEY_RANK = {GREEN: 3, YELLOW: 2, GRAY: 1}
FEEDBACK_CYCLE = (GRAY, YELLOW, GREEN)


@dataclass(frozen=True)
class GuessObservation:
    guess: str
    feedback: FeedbackPattern


def next_feedback_color(current: int) -> int:
    index = FEEDBACK_CYCLE.index(current) if current in FEEDBACK_CYCLE else 0
    return FEEDBACK_CYCLE[(index + 1) % len(FEEDBACK_CYCLE)]


def merge_key_state(current: int | None, incoming: int) -> int:
    """Keyboard keys never downgrade: GREEN > YELLOW > GRAY > UNKNOWN."""
    if current is None:
        return incoming
    if KEY_RANK.get(incoming, 0) > KEY_RANK.get(current, 0):
        return incoming
    return current


def keyboard_from_history(history: list[GuessObservation]) -> dict[str, int]:
    state: dict[str, int] = {}
    for observation in history:
        for letter, color in zip(observation.guess, observation.feedback, strict=True):
            state[letter] = merge_key_state(state.get(letter), color)
    return state


@dataclass
class TurnStat:
    guess: str
    feedback: FeedbackPattern
    entropy: float | None
    candidates_after: int


@dataclass
class AssistedState:
    board: list[list[str]] = field(
        default_factory=lambda: [[""] * WORD_LENGTH for _ in range(MAX_GUESSES)]
    )
    colors: list[list[int | None]] = field(
        default_factory=lambda: [[None] * WORD_LENGTH for _ in range(MAX_GUESSES)]
    )
    current_row: int = 0
    current_col: int = 0
    awaiting_feedback: bool = False
    solved: bool = False
    failed: bool = False
    status_message: str = ""
    history: list[GuessObservation] = field(default_factory=list)
    keyboard: dict[str, int] = field(default_factory=dict)
    turn_stats: list[TurnStat] = field(default_factory=list)
    last_entropy: float | None = None
