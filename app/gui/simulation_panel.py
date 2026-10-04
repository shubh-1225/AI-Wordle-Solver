"""Solver-mode and batch-simulation controls. No ranking math."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from app.gui.styles import ACCENT, ACCENT_HOVER, PANEL_BG, PANEL_BORDER, TEXT_MUTED, TEXT_PRIMARY
from app.solver.simulator import STRATEGIES


def _field_label(parent: ctk.CTkFrame, text: str) -> None:
    ctk.CTkLabel(
        parent,
        text=text,
        text_color=TEXT_MUTED,
        font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
    ).pack(anchor="w", padx=16, pady=(8, 2))


class SolverModePanel(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_run: Callable[[str, str | None, str], None],
        **kwargs: object,
    ) -> None:
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
            text="AI SOLVER MODE",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=TEXT_MUTED,
        ).pack(pady=(14, 4), padx=16, anchor="w")
        ctk.CTkLabel(
            self,
            text="The solver plays a hidden answer on the board.",
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(family="Segoe UI", size=13),
        ).pack(anchor="w", padx=16)
        _field_label(self, "Hidden answer  ·  blank = random")
        self.answer = ctk.CTkEntry(self, placeholder_text="crane")
        self.answer.pack(fill="x", padx=16, pady=4)
        _field_label(self, "Starting word  ·  blank = solver chooses")
        self.opener = ctk.CTkEntry(self, placeholder_text="soare")
        self.opener.pack(fill="x", padx=16, pady=4)
        _field_label(self, "Strategy")
        self.strategy = ctk.CTkOptionMenu(self, values=list(STRATEGIES), fg_color="#2A2C33")
        self.strategy.set("maximum_entropy")
        self.strategy.pack(padx=16, pady=4, anchor="w")
        ctk.CTkButton(
            self,
            text="Start solver",
            command=self._submit,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            height=38,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
        ).pack(padx=16, pady=14, fill="x")
        self.status = ctk.CTkLabel(self, text="", text_color=TEXT_PRIMARY)
        self.status.pack(pady=(0, 12), padx=16)
        self._on_run = on_run

    def _submit(self) -> None:
        opener = self.opener.get().strip().lower() or None
        answer = self.answer.get().strip().lower()
        self._on_run(self.strategy.get(), opener, answer)

    def set_status(self, text: str) -> None:
        self.status.configure(text=text)


class SimulationModePanel(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_run: Callable[[str, str, int], None],
        **kwargs: object,
    ) -> None:
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
            text="SIMULATION",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=TEXT_MUTED,
        ).pack(pady=(14, 4), padx=16, anchor="w")
        ctk.CTkLabel(
            self,
            text="Runs in the background. The window stays usable.",
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(family="Segoe UI", size=13),
        ).pack(anchor="w", padx=16)
        _field_label(self, "Starting word")
        self.opener = ctk.CTkEntry(self, placeholder_text="soare")
        self.opener.insert(0, "soare")
        self.opener.pack(fill="x", padx=16, pady=4)
        _field_label(self, "Strategy")
        self.strategy = ctk.CTkOptionMenu(self, values=list(STRATEGIES), fg_color="#2A2C33")
        self.strategy.set("maximum_entropy")
        self.strategy.pack(padx=16, pady=4, anchor="w")
        _field_label(self, "Number of games")
        self.games = ctk.CTkEntry(self)
        self.games.insert(0, "25")
        self.games.pack(fill="x", padx=16, pady=4)
        ctk.CTkButton(
            self,
            text="Start simulation",
            command=self._submit,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            height=38,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
        ).pack(padx=16, pady=14, fill="x")
        self.progress = ctk.CTkProgressBar(self, progress_color=ACCENT)
        self.progress.set(0)
        self.progress.pack(fill="x", padx=16, pady=(0, 8))
        self.status = ctk.CTkLabel(self, text="Ready.", text_color=TEXT_MUTED)
        self.status.pack(pady=(0, 12), padx=16)
        self._on_run = on_run

    def _submit(self) -> None:
        opener = self.opener.get().strip().lower() or "soare"
        try:
            count = max(1, int(self.games.get().strip()))
        except ValueError:
            count = 25
            self.games.delete(0, "end")
            self.games.insert(0, "25")
            self.status.configure(text="Use a whole number of games. Using 25.")
        self._on_run(self.strategy.get(), opener, count)

    def set_progress(self, done: int, total: int) -> None:
        fraction = 0 if total == 0 else done / total
        self.progress.set(fraction)
        self.status.configure(text=f"{done} / {total} games")
