"""Wordle feedback engine.

Independent of the GUI. Uses Wordle's two-pass duplicate-letter rules:
greens are assigned first, then unused answer letters are used for yellows.
"""

from __future__ import annotations

from collections import Counter

from app.models.feedback import (
    GRAY,
    GREEN,
    WORD_LENGTH,
    YELLOW,
    FeedbackPattern,
)


class FeedbackError(ValueError):
    """Raised when a guess or answer cannot be scored."""


class FeedbackEngine:
    """Score a guess against an answer using official Wordle coloring."""

    def get_feedback(self, guess: str, answer: str) -> FeedbackPattern:
        guess_word = normalize_word(guess, label="guess")
        answer_word = normalize_word(answer, label="answer")

        pattern = [GRAY] * WORD_LENGTH
        unused_answer_letters: Counter[str] = Counter()

        for index, (guess_letter, answer_letter) in enumerate(zip(guess_word, answer_word)):
            if guess_letter == answer_letter:
                pattern[index] = GREEN
            else:
                unused_answer_letters[answer_letter] += 1

        for index, guess_letter in enumerate(guess_word):
            if pattern[index] == GREEN:
                continue
            if unused_answer_letters[guess_letter] > 0:
                pattern[index] = YELLOW
                unused_answer_letters[guess_letter] -= 1

        return (pattern[0], pattern[1], pattern[2], pattern[3], pattern[4])


def normalize_word(word: str, *, label: str) -> str:
    if not isinstance(word, str):
        raise FeedbackError(f"{label} must be a string")
    normalized = word.strip().lower()
    if len(normalized) != WORD_LENGTH:
        raise FeedbackError(
            f"{label} must be exactly {WORD_LENGTH} letters, got {word!r}"
        )
    if not normalized.isascii() or not normalized.isalpha():
        raise FeedbackError(
            f"{label} must contain only alphabetic characters, got {word!r}"
        )
    return normalized


_ENGINE = FeedbackEngine()


def get_feedback(guess: str, answer: str) -> FeedbackPattern:
    """Return a length-5 pattern of 0 (gray), 1 (yellow), and 2 (green)."""
    return _ENGINE.get_feedback(guess, answer)
