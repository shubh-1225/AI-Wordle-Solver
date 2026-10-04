"""Feedback helper label. Color cycling lives on the board tiles."""

from __future__ import annotations

import customtkinter as ctk

from app.gui.styles import ACCENT, ACCENT_HOVER, TEXT_MUTED


class FeedbackSelector(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_submit: object,
        **kwargs: object,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.hint = ctk.CTkLabel(
            self,
            text="Enter a 5-letter guess, then click tiles: gray → yellow → green",
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(family="Segoe UI", size=13),
        )
        self.hint.pack(side="left", padx=8)
        self.submit = ctk.CTkButton(
            self,
            text="Submit feedback",
            command=on_submit,
            width=168,
            height=36,
            corner_radius=8,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        )
        self.submit.pack(side="right", padx=8)

    def set_hint(self, text: str) -> None:
        self.hint.configure(text=text)
