"""AI recommendation, metrics, and candidate list. Display only."""

from __future__ import annotations

from collections.abc import Sequence

import customtkinter as ctk

from app.gui.styles import ACCENT, PANEL_BG, PANEL_BORDER, TEXT_MUTED, TEXT_PRIMARY
from app.models.recommendation import Recommendation


class SolverPanel(ctk.CTkFrame):
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
            text="AI RECOMMENDATION",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=TEXT_MUTED,
        ).pack(pady=(10, 0), padx=12, anchor="w")

        self.best_guess = ctk.CTkLabel(
            self,
            text="—",
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color=TEXT_PRIMARY,
        )
        self.best_guess.pack(pady=(0, 4))

        metrics = ctk.CTkFrame(self, fg_color="transparent")
        metrics.pack(fill="x", padx=8, pady=(0, 2))
        metrics.grid_columnconfigure((0, 1), weight=1)

        self.remaining_caption, self.remaining_value = self._metric(
            metrics, 0, 0, "Candidates"
        )
        self.entropy_caption, self.entropy = self._metric(metrics, 0, 1, "Entropy")
        self.groups_caption, self.groups = self._metric(metrics, 1, 0, "Feedback groups")
        self.reduction_caption, self.reduction = self._metric(metrics, 1, 1, "Expected reduction")
        self.candidate_count = ctk.CTkLabel(self, text="Possible answers remaining: 0")

        ctk.CTkLabel(
            self,
            text="OTHER STRONG GUESSES",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=TEXT_MUTED,
        ).pack(pady=(2, 0), padx=12, anchor="w")
        self.alternatives = ctk.CTkLabel(
            self,
            text="—",
            justify="left",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=TEXT_PRIMARY,
        )
        self.alternatives.pack(padx=12, pady=(0, 8), anchor="w")

        self._candidates: tuple[str, ...] = ()
        self.list_frame: ctk.CTkFrame | None = None
        self.search: ctk.CTkEntry | None = None
        self.list_label: ctk.CTkLabel | None = None
        self.listbox: ctk.CTkTextbox | None = None

    def attach_candidates(self, parent: ctk.CTkBaseClass) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(
            parent,
            fg_color=PANEL_BG,
            corner_radius=12,
            border_width=1,
            border_color=PANEL_BORDER,
        )
        ctk.CTkLabel(
            frame,
            text="CURRENT POSSIBILITIES",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=TEXT_MUTED,
        ).pack(pady=(8, 2), padx=12, anchor="w")
        self.search = ctk.CTkEntry(
            frame,
            placeholder_text="Filter candidates",
            border_color=PANEL_BORDER,
            fg_color="#121318",
            height=28,
        )
        self.search.pack(fill="x", padx=12)
        self.search.bind("<KeyRelease>", lambda _event: self._apply_filter())
        self.list_label = ctk.CTkLabel(
            frame,
            text="Showing top 50",
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=11),
        )
        self.list_label.pack(anchor="w", padx=12)
        self.listbox = ctk.CTkTextbox(
            frame,
            height=140,
            activate_scrollbars=True,
            fg_color="#121318",
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family="Consolas", size=13),
        )
        self.listbox.pack(fill="both", expand=True, padx=12, pady=(2, 10))
        self.list_frame = frame
        return frame

    def _metric(
        self,
        parent: ctk.CTkFrame,
        row: int,
        column: int,
        caption: str,
    ) -> tuple[ctk.CTkLabel, ctk.CTkLabel]:
        card = ctk.CTkFrame(parent, fg_color="#121318", corner_radius=8, border_width=1, border_color=PANEL_BORDER)
        card.grid(row=row, column=column, sticky="nsew", padx=3, pady=3)
        title = ctk.CTkLabel(
            card,
            text=caption,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=TEXT_MUTED,
        )
        title.pack(anchor="w", padx=8, pady=(4, 0))
        value = ctk.CTkLabel(
            card,
            text="—",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=ACCENT if caption == "Candidates" else TEXT_PRIMARY,
        )
        value.pack(anchor="w", padx=8, pady=(0, 4))
        return title, value

    def set_loading(self, remaining: int | None = None) -> None:
        self.best_guess.configure(text="…")
        if remaining is not None:
            self.remaining_value.configure(text=str(remaining))
            self.candidate_count.configure(text=f"Possible answers remaining: {remaining}")
        self.entropy.configure(text="…")
        self.groups.configure(text="…")
        self.reduction.configure(text="…")

    def render_recommendation(
        self,
        recommendation: Recommendation | None,
        candidates: Sequence[str],
    ) -> None:
        self._candidates = tuple(candidates)
        count = len(candidates)
        self.remaining_value.configure(text=str(count))
        self.candidate_count.configure(text=f"Possible answers remaining: {count}")
        if recommendation is None:
            self.best_guess.configure(text="—")
            self.entropy.configure(text="—")
            self.groups.configure(text="—")
            self.reduction.configure(text="—")
            self.alternatives.configure(text="—")
        else:
            self.best_guess.configure(text=recommendation.best_guess.upper())
            self.entropy.configure(text=f"{recommendation.entropy:.2f} bits")
            self.groups.configure(text=str(recommendation.feedback_groups))
            self.reduction.configure(text=f"{recommendation.expected_reduction * 100:.1f}%")
            others = recommendation.ranked_guesses[1:5]
            self.alternatives.configure(
                text="   ".join(score.guess.upper() for score in others) if others else "—"
            )
        self._apply_filter()

    def _apply_filter(self) -> None:
        if self.listbox is None or self.list_label is None or self.search is None:
            return
        query = self.search.get().strip().lower()
        words = [word for word in self._candidates if query in word]
        shown = words[:50]
        extra = "" if len(words) <= 50 else f" of {len(words)}"
        self.list_label.configure(text=f"Showing {len(shown)}{extra}")
        self.listbox.delete("1.0", "end")
        if not shown:
            self.listbox.insert("end", "No matching candidates")
            return
        for index, word in enumerate(shown, start=1):
            self.listbox.insert("end", f"{index:>2}.  {word.upper()}\n")
