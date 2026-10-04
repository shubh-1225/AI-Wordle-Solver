"""Application session: coordinates solver calls for the GUI.

GUI classes must not compute entropy or filter candidates. They call this
session, which delegates ranking/filtering to WordleSolver.
"""

from __future__ import annotations

from dataclasses import dataclass
import threading

from app.models.feedback import GRAY, GREEN, WORD_LENGTH, FeedbackPattern
from app.models.game import (
    AssistedState,
    GuessObservation,
    TurnStat,
    keyboard_from_history,
    next_feedback_color,
)
from app.models.recommendation import Recommendation
from app.solver.constraints import ContradictoryFeedbackError, ConstraintError
from app.solver.solver import WordleSolver
from app.utils.config import MAX_GUESSES


@dataclass(frozen=True)
class SessionError:
    message: str


class GameSession:
    """Assisted Wordle session backed by a WordleSolver instance."""

    def __init__(self, solver: WordleSolver) -> None:
        self.solver = solver
        self.allowed = frozenset(solver.allowed_guesses)
        self.state = AssistedState()
        self._lock = threading.Lock()

    def new_game(self) -> None:
        with self._lock:
            self.solver.reset()
        self.state = AssistedState()

    def reset_current_row(self) -> None:
        if self.state.solved or self.state.failed:
            return
        if self.state.awaiting_feedback:
            row = self.state.current_row
            self.state.board[row] = [""] * WORD_LENGTH
            self.state.colors[row] = [None] * WORD_LENGTH
            self.state.awaiting_feedback = False
            self.state.current_col = 0
            self.state.status_message = ""
            return
        row = self.state.current_row
        self.state.board[row] = [""] * WORD_LENGTH
        self.state.current_col = 0
        self.state.status_message = ""

    def type_letter(self, letter: str) -> None:
        if self._locked():
            return
        if self.state.awaiting_feedback:
            return
        ch = letter.strip().lower()
        if len(ch) != 1 or not ch.isalpha():
            return
        if self.state.current_col >= WORD_LENGTH:
            return
        row = self.state.current_row
        col = self.state.current_col
        self.state.board[row][col] = ch
        self.state.current_col += 1
        self.state.status_message = ""

    def backspace(self) -> None:
        if self._locked() or self.state.awaiting_feedback:
            return
        if self.state.current_col <= 0:
            return
        self.state.current_col -= 1
        row = self.state.current_row
        col = self.state.current_col
        self.state.board[row][col] = ""
        self.state.status_message = ""

    def submit_guess(self) -> SessionError | None:
        if self._locked():
            return SessionError("Game already finished.")
        if self.state.awaiting_feedback:
            return None
        row = self.state.current_row
        guess = "".join(self.state.board[row])
        if len(guess) != WORD_LENGTH:
            return SessionError("Not enough letters")
        if guess not in self.allowed:
            return SessionError("Not in word list")
        if any(obs.guess == guess for obs in self.state.history):
            return SessionError("Already guessed")
        self.state.colors[row] = [GRAY] * WORD_LENGTH
        self.state.awaiting_feedback = True
        self.state.status_message = "Click tiles to set colors, then submit feedback."
        return None

    def cycle_tile(self, row: int, col: int) -> None:
        if not self.state.awaiting_feedback:
            return
        if row != self.state.current_row:
            return
        current = self.state.colors[row][col]
        if current is None:
            current = GRAY
        self.state.colors[row][col] = next_feedback_color(current)

    def current_feedback(self) -> FeedbackPattern | None:
        if not self.state.awaiting_feedback:
            return None
        row = self.state.current_row
        values = self.state.colors[row]
        if any(value is None for value in values):
            return None
        return (values[0], values[1], values[2], values[3], values[4])  # type: ignore[return-value]

    def submit_feedback(self) -> SessionError | None:
        if self._locked():
            return SessionError("Game already finished.")
        if not self.state.awaiting_feedback:
            return SessionError("Enter a guess first.")
        feedback = self.current_feedback()
        if feedback is None:
            return SessionError("Set a color on every tile.")
        row = self.state.current_row
        guess = "".join(self.state.board[row])
        try:
            with self._lock:
                try:
                    entropy = self.solver.get_entropy(guess)
                except ConstraintError:
                    entropy = None
                remaining = self.solver.update(guess, feedback)
        except (ContradictoryFeedbackError, ConstraintError) as exc:
            return SessionError(str(exc))

        observation = GuessObservation(guess=guess, feedback=feedback)
        self.state.history.append(observation)
        self.state.keyboard = keyboard_from_history(self.state.history)
        self.state.turn_stats.append(
            TurnStat(
                guess=guess,
                feedback=feedback,
                entropy=entropy,
                candidates_after=len(remaining),
            )
        )
        self.state.last_entropy = entropy
        self.state.awaiting_feedback = False

        if feedback == (GREEN,) * WORD_LENGTH:
            self.state.solved = True
            self.state.status_message = f"Solved in {len(self.state.history)} guesses."
            return None
        if not remaining:
            self.state.failed = True
            self.state.status_message = (
                "No possible answers match the feedback entered. "
                "Please check the feedback colors and previous guesses."
            )
            return None
        if self.state.current_row >= MAX_GUESSES - 1:
            self.state.failed = True
            self.state.status_message = "Six guesses exhausted."
            return None
        self.state.current_row += 1
        self.state.current_col = 0
        self.state.status_message = ""
        return None

    def candidates(self) -> tuple[str, ...]:
        with self._lock:
            return self.solver.get_candidates()

    def recommendation(self, limit: int = 5) -> Recommendation | None:
        with self._lock:
            candidates = self.solver.get_candidates()
            if not candidates:
                return None
            return self.solver.get_recommendation(limit=limit)

    def play_recorded_turn(
        self,
        guess: str,
        feedback: FeedbackPattern,
        entropy: float | None,
    ) -> None:
        """Apply a solver-produced turn onto the board (autonomous modes)."""
        row = len(self.state.history)
        if row >= MAX_GUESSES:
            return
        self.state.board[row] = list(guess)
        self.state.colors[row] = list(feedback)
        with self._lock:
            remaining = self.solver.update(guess, feedback)
        observation = GuessObservation(guess=guess, feedback=feedback)
        self.state.history.append(observation)
        self.state.keyboard = keyboard_from_history(self.state.history)
        self.state.turn_stats.append(
            TurnStat(
                guess=guess,
                feedback=feedback,
                entropy=entropy,
                candidates_after=len(remaining),
            )
        )
        self.state.last_entropy = entropy
        self.state.awaiting_feedback = False
        if feedback == (GREEN,) * WORD_LENGTH:
            self.state.solved = True
            self.state.status_message = f"Solved in {len(self.state.history)} guesses."
            return
        if not remaining or row >= MAX_GUESSES - 1:
            self.state.failed = not remaining or row >= MAX_GUESSES - 1
            if not remaining:
                self.state.status_message = (
                    "No possible answers match the feedback entered. "
                    "Please check the feedback colors and previous guesses."
                )
            else:
                self.state.status_message = "Six guesses exhausted."
            return
        self.state.current_row = row + 1
        self.state.current_col = 0
        self.state.status_message = ""

    def _locked(self) -> bool:
        return self.state.solved or self.state.failed
