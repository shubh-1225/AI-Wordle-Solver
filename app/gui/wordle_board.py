"""5x6 Wordle board. Rendering only."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from app.gui.styles import (
    TEXT_PRIMARY,
    TILE_BORDER,
    TILE_BORDER_ACTIVE,
    TILE_COLORS,
    TILE_EMPTY,
    TILE_HOVER,
)
from app.models.feedback import WORD_LENGTH
from app.models.game import AssistedState
from app.utils.config import MAX_GUESSES

TILE_SIZE = 62


class WordleBoard(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_tile_click: Callable[[int, int], None],
        **kwargs: object,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._tiles: list[list[ctk.CTkButton]] = []
        self._prev: list[list[tuple[str, int | None]]] = [
            [("", None)] * WORD_LENGTH for _ in range(MAX_GUESSES)
        ]
        for row in range(MAX_GUESSES):
            row_frame = ctk.CTkFrame(self, fg_color="transparent")
            row_frame.pack(pady=3)
            buttons: list[ctk.CTkButton] = []
            for col in range(WORD_LENGTH):
                button = ctk.CTkButton(
                    row_frame,
                    text="",
                    width=TILE_SIZE,
                    height=TILE_SIZE,
                    corner_radius=6,
                    fg_color=TILE_EMPTY,
                    border_width=2,
                    border_color=TILE_BORDER,
                    text_color=TEXT_PRIMARY,
                    font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
                    hover=True,
                    hover_color=TILE_HOVER[None],
                    command=lambda r=row, c=col: on_tile_click(r, c),
                )
                button.pack(side="left", padx=4)
                buttons.append(button)
            self._tiles.append(buttons)

    def render(self, state: AssistedState) -> None:
        coloring = state.awaiting_feedback
        for row in range(MAX_GUESSES):
            current_row = row == state.current_row and not state.solved
            for col in range(WORD_LENGTH):
                letter = state.board[row][col]
                color = state.colors[row][col]
                tile = self._tiles[row][col]
                filled = bool(letter)
                border = TILE_COLORS[color] if color is not None else (
                    TILE_BORDER_ACTIVE if filled or (current_row and col == state.current_col)
                    else TILE_BORDER
                )
                tile.configure(
                    text=letter.upper(),
                    fg_color=TILE_COLORS.get(color, TILE_EMPTY),
                    border_color=border,
                    hover_color=TILE_HOVER.get(color, TILE_HOVER[None]) if coloring else TILE_COLORS.get(color, TILE_EMPTY),
                )
                prev_letter, _prev_color = self._prev[row][col]
                if letter and letter != prev_letter and color is None:
                    self._pop(tile)
                self._prev[row][col] = (letter, color)

    def _pop(self, tile: ctk.CTkButton) -> None:
        tile.configure(width=TILE_SIZE + 6, height=TILE_SIZE + 6)
        tile.after(80, lambda: tile.configure(width=TILE_SIZE, height=TILE_SIZE) if tile.winfo_exists() else None)
