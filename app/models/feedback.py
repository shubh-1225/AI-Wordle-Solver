"""Wordle feedback pattern values."""

from __future__ import annotations

from typing import Final

GRAY: Final[int] = 0
YELLOW: Final[int] = 1
GREEN: Final[int] = 2

WORD_LENGTH: Final[int] = 5
PATTERN_COUNT: Final[int] = 3**WORD_LENGTH  # 243

FeedbackPattern = tuple[int, int, int, int, int]
