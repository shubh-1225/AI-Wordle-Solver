"""On-screen QWERTY keyboard. Rendering and click callbacks only."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from app.gui.styles import KEY_COLORS, KEY_HOVER, KEY_TEXT, QWERTY_ROWS, TEXT_PRIMARY


class OnScreenKeyboard(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_letter: Callable[[str], None],
        on_enter: Callable[[], None],
        on_backspace: Callable[[], None],
        **kwargs: object,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._keys: dict[str, ctk.CTkButton] = {}
        self._action_keys: list[ctk.CTkButton] = []

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack()
        for letter in QWERTY_ROWS[0]:
            self._add_key(top, letter, on_letter, width=42)

        middle = ctk.CTkFrame(self, fg_color="transparent")
        middle.pack(pady=6)
        for letter in QWERTY_ROWS[1]:
            self._add_key(middle, letter, on_letter, width=42)

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack()
        enter = self._action_button(bottom, "ENTER", on_enter, width=78)
        enter.pack(side="left", padx=3)
        self._action_keys.append(enter)
        for letter in QWERTY_ROWS[2]:
            self._add_key(bottom, letter, on_letter, width=42)
        back = self._action_button(bottom, "⌫", on_backspace, width=60)
        back.pack(side="left", padx=3)
        self._action_keys.append(back)

    def _add_key(
        self,
        parent: ctk.CTkFrame,
        letter: str,
        on_letter: Callable[[str], None],
        *,
        width: int,
    ) -> None:
        button = ctk.CTkButton(
            parent,
            text=letter.upper(),
            width=width,
            height=52,
            corner_radius=8,
            command=lambda ch=letter: on_letter(ch),
            fg_color=KEY_COLORS[None],
            hover_color=KEY_HOVER[None],
            text_color=KEY_TEXT,
            hover=True,
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
        )
        button.pack(side="left", padx=3)
        self._keys[letter] = button

    def _action_button(
        self,
        parent: ctk.CTkFrame,
        text: str,
        command: Callable[[], None],
        *,
        width: int,
    ) -> ctk.CTkButton:
        return ctk.CTkButton(
            parent,
            text=text,
            width=width,
            height=52,
            corner_radius=8,
            command=command,
            fg_color="#565758",
            hover_color="#6C6D6E",
            text_color=TEXT_PRIMARY,
            hover=True,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        )

    def render(self, keyboard: dict[str, int]) -> None:
        for letter, button in self._keys.items():
            color = keyboard.get(letter)
            button.configure(
                fg_color=KEY_COLORS.get(color, KEY_COLORS[None]),
                hover_color=KEY_HOVER.get(color, KEY_HOVER[None]),
            )
