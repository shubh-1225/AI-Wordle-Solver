"""Load and validate external Wordle word lists."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.utils.config import ALLOWED_GUESSES_PATH, ANSWERS_PATH


class WordListError(ValueError):
    """Raised when a word list file is missing or invalid."""


@dataclass(frozen=True)
class WordData:
    answers: tuple[str, ...]
    allowed_guesses: tuple[str, ...]


def _validate_word(word: str, *, label: str, lineno: int) -> None:
    if word != word.lower():
        raise WordListError(
            f"{label} line {lineno}: word must be lowercase, got {word!r}"
        )
    if len(word) != 5:
        raise WordListError(
            f"{label} line {lineno}: word must be exactly 5 letters, got {word!r}"
        )
    if not word.isascii() or not word.isalpha():
        raise WordListError(
            f"{label} line {lineno}: word must contain only alphabetic characters, got {word!r}"
        )


def load_word_file(path: Path, *, label: str) -> tuple[str, ...]:
    if not path.is_file():
        raise WordListError(f"Missing {label} file: {path}")

    words: list[str] = []
    seen: set[str] = set()
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        word = line.strip()
        if not word:
            continue
        _validate_word(word, label=label, lineno=lineno)
        if word in seen:
            raise WordListError(f"{label} line {lineno}: duplicate word {word!r}")
        seen.add(word)
        words.append(word)

    if not words:
        raise WordListError(f"{label} file is empty: {path}")

    return tuple(words)


def validate_answer_subset(answers: tuple[str, ...], allowed_guesses: tuple[str, ...]) -> None:
    allowed = set(allowed_guesses)
    missing = [word for word in answers if word not in allowed]
    if missing:
        preview = ", ".join(missing[:10])
        raise WordListError(
            "Every answer must exist in allowed_guesses.txt. "
            f"Missing {len(missing)} word(s), including: {preview}"
        )


def load_word_data(
    answers_path: Path | None = None,
    allowed_guesses_path: Path | None = None,
) -> WordData:
    answers = load_word_file(answers_path or ANSWERS_PATH, label="answers")
    allowed_guesses = load_word_file(
        allowed_guesses_path or ALLOWED_GUESSES_PATH,
        label="allowed guesses",
    )
    validate_answer_subset(answers, allowed_guesses)
    return WordData(answers=answers, allowed_guesses=allowed_guesses)
