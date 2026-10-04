"""Compact, always-visible game statistics. Display only."""

from __future__ import annotations

import customtkinter as ctk

from app.gui.styles import PANEL_BG, PANEL_BORDER, TEXT_MUTED, TEXT_PRIMARY
from app.models.game import AssistedState
from app.models.statistics import BenchmarkSummary, SimulationResult
from app.utils.config import MAX_GUESSES


class StatisticsPanel(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass, **kwargs: object) -> None:
        super().__init__(
            master,
            fg_color=PANEL_BG,
            corner_radius=12,
            border_width=1,
            border_color=PANEL_BORDER,
            **kwargs,
        )
        ctk.CTkLabel(
            self,
            text="GAME STATISTICS",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=TEXT_MUTED,
        ).pack(pady=(8, 2), padx=12, anchor="w")

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x", padx=8, pady=(0, 4))
        grid.grid_columnconfigure((1, 3), weight=1)

        self.guess = self._row(grid, 0, 0, "Guess")
        self.candidates = self._row(grid, 0, 2, "Candidates")
        self.info = self._row(grid, 1, 0, "Info gained")
        self.status = self._row(grid, 1, 2, "Status")
        self.detail = ctk.CTkLabel(
            self,
            text="",
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            anchor="w",
            justify="left",
        )
        self.detail.pack(fill="x", padx=12, pady=(0, 8))

    def _row(self, parent: ctk.CTkFrame, row: int, column: int, caption: str) -> ctk.CTkLabel:
        ctk.CTkLabel(
            parent,
            text=caption,
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            anchor="w",
        ).grid(row=row, column=column, sticky="w", padx=(8, 6), pady=2)
        value = ctk.CTkLabel(
            parent,
            text="—",
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            anchor="w",
        )
        value.grid(row=row, column=column + 1, sticky="w", padx=(0, 12), pady=2)
        return value

    def render_game(self, state: AssistedState, remaining: int) -> None:
        guess_number = min(len(state.history) + (0 if state.solved or state.failed else 1), MAX_GUESSES)
        if state.solved or state.failed:
            guess_number = len(state.history)
        self.guess.configure(text=f"{guess_number} / {MAX_GUESSES}")
        self.candidates.configure(text=str(remaining))
        entropies = [turn.entropy for turn in state.turn_stats if turn.entropy is not None]
        gained = sum(entropies) if entropies else 0.0
        average = (gained / len(entropies)) if entropies else 0.0
        self.info.configure(text=f"{gained:.2f} bits")
        if state.solved:
            status = "Solved"
        elif state.failed:
            status = "Failed"
        elif state.awaiting_feedback:
            status = "Set colors"
        else:
            status = "In progress"
        self.status.configure(text=status)
        extra = f"Guesses: {len(state.history)}"
        if entropies:
            extra += f"    Avg entropy: {average:.2f} bits"
        if state.solved and state.history:
            extra += f"    Answer: {state.history[-1].guess.upper()}"
        self.detail.configure(text=extra)

    def render_simulation(self, result: SimulationResult) -> None:
        self.guess.configure(text=f"{result.guesses} / {MAX_GUESSES}")
        last = result.turns[-1].candidates_after if result.turns else 0
        self.candidates.configure(text=str(last))
        entropies = [turn.entropy for turn in result.turns if turn.entropy is not None]
        gained = sum(entropies) if entropies else 0.0
        self.info.configure(text=f"{gained:.2f} bits")
        self.status.configure(text="Solved" if result.solved else "Failed")
        opener = (result.starting_word or "—").upper()
        self.detail.configure(
            text=f"Answer: {result.answer.upper()}    Opener: {opener}    Strategy: {result.strategy}"
        )

    def render_benchmark(self, summary: BenchmarkSummary) -> None:
        self.guess.configure(text=f"{summary.average_guesses:.2f} avg")
        self.candidates.configure(text=str(summary.games))
        self.info.configure(text=f"{summary.win_rate:.1%} win")
        self.status.configure(text="Sim done")
        self.detail.configure(
            text=(
                f"Median {summary.median_guesses:.1f}    "
                f"Worst {summary.maximum_guesses}    "
                f"Failed {summary.failed}    "
                f"Opener {summary.starting_word or '—'}"
            )
        )
