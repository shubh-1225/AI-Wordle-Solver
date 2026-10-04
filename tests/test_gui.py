"""Headless smoke test of the CustomTkinter window."""

from __future__ import annotations

from app.gui.main_window import MainWindow
from app.models.feedback import GRAY, GREEN, YELLOW
from app.session import GameSession
from app.solver.feedback import get_feedback
from app.solver.solver import WordleSolver


def test_main_window_assisted_flow() -> None:
    answers = ("crane", "slate", "audio", "house")
    allowed = answers + ("zzzzz",)
    session = GameSession(WordleSolver(answers, allowed, cache=False))
    window = MainWindow(session)
    window.withdraw()
    window.update()
    try:
        for letter in "slate":
            window.type_letter(letter)
        window.update()
        assert session.state.board[0] == list("slate")
        window.on_enter()
        window.update()
        assert session.state.awaiting_feedback is True
        pattern = get_feedback("slate", "crane")
        session.state.colors[0] = list(pattern)
        window.submit_feedback()
        window.update()
        for _ in range(20):
            window.update()
        assert session.state.history[0].guess == "slate"
        assert session.candidates()
        assert window.solver_panel.candidate_count.cget("text").startswith(
            "Possible answers remaining:"
        )
        assert window.board._tiles[0][0].cget("text") == "S"
        assert YELLOW in pattern or GREEN in pattern or GRAY in pattern
    finally:
        window.destroy()
