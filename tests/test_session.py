"""Tests for assisted-play session state (no GUI)."""

from __future__ import annotations

from app.models.feedback import GRAY, GREEN, YELLOW
from app.models.game import keyboard_from_history, merge_key_state, next_feedback_color
from app.models.game import GuessObservation
from app.session import GameSession
from app.solver.solver import WordleSolver


def test_feedback_cycles_gray_yellow_green() -> None:
    assert next_feedback_color(GRAY) == YELLOW
    assert next_feedback_color(YELLOW) == GREEN
    assert next_feedback_color(GREEN) == GRAY


def test_keyboard_never_downgrades() -> None:
    assert merge_key_state(None, GRAY) == GRAY
    assert merge_key_state(GRAY, YELLOW) == YELLOW
    assert merge_key_state(YELLOW, GRAY) == YELLOW
    assert merge_key_state(GREEN, YELLOW) == GREEN
    history = [
        GuessObservation("sassy", (GRAY, GRAY, GRAY, GRAY, GRAY)),
        GuessObservation("raise", (YELLOW, GRAY, GRAY, YELLOW, GRAY)),
    ]
    keys = keyboard_from_history(history)
    assert keys["s"] == YELLOW


def test_session_rejects_invalid_word() -> None:
    solver = WordleSolver(("crane", "slate"), ("crane", "slate"), cache=False)
    session = GameSession(solver)
    for letter in "abcde":
        session.type_letter(letter)
    error = session.submit_guess()
    assert error is not None
    assert error.message == "Not in word list"
    assert session.state.awaiting_feedback is False


def test_session_submit_feedback_filters_candidates() -> None:
    solver = WordleSolver(("crane", "slate", "audio"), ("crane", "slate", "audio"), cache=False)
    session = GameSession(solver)
    for letter in "slate":
        session.type_letter(letter)
    assert session.submit_guess() is None
    session.state.colors[0] = [GRAY, GRAY, GRAY, GRAY, GRAY]
    assert session.submit_feedback() is None
    assert "slate" not in session.candidates()
    assert session.state.history[0].guess == "slate"
    assert session.state.keyboard["s"] == GRAY
