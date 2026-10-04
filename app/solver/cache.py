"""Precomputed Wordle feedback patterns encoded as base-3 integers 0–242."""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from app.models.feedback import PATTERN_COUNT, WORD_LENGTH, FeedbackPattern
from app.solver.feedback import FeedbackEngine, get_feedback
from app.utils.config import FEEDBACK_CACHE_PATH

CACHE_VERSION = 1


class CacheError(ValueError):
    """Raised when a feedback cache cannot be used."""


def encode_pattern(pattern: Sequence[int]) -> int:
    """Encode five ternary feedback digits as an integer in 0..242."""
    if len(pattern) != WORD_LENGTH:
        raise CacheError(f"pattern must have {WORD_LENGTH} values")
    code = 0
    for value in pattern:
        if value not in (0, 1, 2):
            raise CacheError(f"invalid feedback value {value!r}")
        code = code * 3 + int(value)
    return code


def decode_pattern(code: int) -> FeedbackPattern:
    if not 0 <= code < PATTERN_COUNT:
        raise CacheError(f"encoded pattern must be 0..{PATTERN_COUNT - 1}, got {code}")
    values = [0] * WORD_LENGTH
    remaining = int(code)
    for index in range(WORD_LENGTH - 1, -1, -1):
        remaining, values[index] = divmod(remaining, 3)
    return (values[0], values[1], values[2], values[3], values[4])


def word_list_fingerprint(words: Sequence[str]) -> str:
    payload = "\n".join(words).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _as_word_tuple(values: np.ndarray) -> tuple[str, ...]:
    return tuple(str(word) for word in values.tolist())


@dataclass
class FeedbackPatternCache:
    guesses: tuple[str, ...]
    answers: tuple[str, ...]
    matrix: np.ndarray
    guesses_sha256: str
    answers_sha256: str

    def __post_init__(self) -> None:
        self._guess_index = {word: index for index, word in enumerate(self.guesses)}
        self._answer_index = {word: index for index, word in enumerate(self.answers)}
        if self.matrix.dtype != np.uint8:
            raise CacheError("feedback matrix must be uint8")
        if self.matrix.shape != (len(self.guesses), len(self.answers)):
            raise CacheError(
                f"matrix shape {self.matrix.shape} does not match "
                f"({len(self.guesses)}, {len(self.answers)})"
            )

    def guess_index(self, guess: str) -> int | None:
        return self._guess_index.get(guess)

    def candidate_columns(self, candidates: Sequence[str]) -> np.ndarray | None:
        try:
            return np.fromiter(
                (self._answer_index[word] for word in candidates),
                dtype=np.int32,
                count=len(candidates),
            )
        except KeyError:
            return None

    def encoded_feedback(self, guess: str, answer: str) -> int:
        guess_idx = self._guess_index.get(guess)
        answer_idx = self._answer_index.get(answer)
        if guess_idx is None or answer_idx is None:
            raise CacheError(f"pair ({guess!r}, {answer!r}) is not in the cache")
        return int(self.matrix[guess_idx, answer_idx])

    def feedback(self, guess: str, answer: str) -> FeedbackPattern:
        return decode_pattern(self.encoded_feedback(guess, answer))

    def encoded_row(self, guess: str, candidates: Sequence[str]) -> np.ndarray | None:
        guess_idx = self.guess_index(guess)
        columns = self.candidate_columns(candidates)
        if guess_idx is None or columns is None:
            return None
        return self.matrix[guess_idx, columns]

    def matches_word_lists(
        self,
        guesses: Sequence[str] | None = None,
        answers: Sequence[str] | None = None,
    ) -> bool:
        if guesses is not None and word_list_fingerprint(guesses) != self.guesses_sha256:
            return False
        if answers is not None and word_list_fingerprint(answers) != self.answers_sha256:
            return False
        return True


_CACHE: FeedbackPatternCache | None = None
_CACHE_LOAD_ATTEMPTED = False


def reset_pattern_cache() -> None:
    """Clear the process-wide cache (used by tests)."""
    global _CACHE, _CACHE_LOAD_ATTEMPTED
    _CACHE = None
    _CACHE_LOAD_ATTEMPTED = False


def set_pattern_cache(cache: FeedbackPatternCache | None) -> None:
    global _CACHE, _CACHE_LOAD_ATTEMPTED
    _CACHE = cache
    _CACHE_LOAD_ATTEMPTED = True


def get_pattern_cache() -> FeedbackPatternCache | None:
    global _CACHE, _CACHE_LOAD_ATTEMPTED
    if not _CACHE_LOAD_ATTEMPTED:
        _CACHE_LOAD_ATTEMPTED = True
        _CACHE = load_pattern_cache()
    return _CACHE


def load_pattern_cache(path: Path | None = None) -> FeedbackPatternCache | None:
    cache_path = path or FEEDBACK_CACHE_PATH
    if not cache_path.is_file():
        return None
    try:
        return load_pattern_cache_file(cache_path)
    except (CacheError, OSError, ValueError, KeyError):
        return None


def load_pattern_cache_file(path: Path) -> FeedbackPatternCache:
    try:
        with np.load(path, allow_pickle=False) as data:
            version = int(data["version"])
            if version != CACHE_VERSION:
                raise CacheError(f"unsupported cache version {version}")
            guesses = _as_word_tuple(data["guesses"])
            answers = _as_word_tuple(data["answers"])
            matrix = np.array(data["matrix"], dtype=np.uint8, copy=True)
            guesses_sha256 = str(np.asarray(data["guesses_sha256"]).item())
            answers_sha256 = str(np.asarray(data["answers_sha256"]).item())
    except (OSError, ValueError, KeyError) as exc:
        raise CacheError(f"corrupt feedback cache: {path}") from exc

    cache = FeedbackPatternCache(
        guesses=guesses,
        answers=answers,
        matrix=matrix,
        guesses_sha256=guesses_sha256,
        answers_sha256=answers_sha256,
    )
    if cache.guesses_sha256 != word_list_fingerprint(guesses):
        raise CacheError("guess list fingerprint does not match cache contents")
    if cache.answers_sha256 != word_list_fingerprint(answers):
        raise CacheError("answer list fingerprint does not match cache contents")
    if cache.matrix.size and int(cache.matrix.max()) >= PATTERN_COUNT:
        raise CacheError("cache contains an invalid encoded pattern")
    return cache


def save_pattern_cache(cache: FeedbackPatternCache, path: Path | None = None) -> Path:
    cache_path = path or FEEDBACK_CACHE_PATH
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        cache_path,
        version=np.int32(CACHE_VERSION),
        guesses=np.asarray(cache.guesses, dtype="U5"),
        answers=np.asarray(cache.answers, dtype="U5"),
        matrix=cache.matrix,
        guesses_sha256=np.asarray(cache.guesses_sha256),
        answers_sha256=np.asarray(cache.answers_sha256),
    )
    return cache_path


def build_pattern_cache(
    guesses: Sequence[str],
    answers: Sequence[str],
    *,
    progress: Callable[[int, int], None] | None = None,
) -> FeedbackPatternCache:
    engine = FeedbackEngine()
    matrix = np.empty((len(guesses), len(answers)), dtype=np.uint8)
    for guess_index, guess in enumerate(guesses):
        for answer_index, answer in enumerate(answers):
            matrix[guess_index, answer_index] = encode_pattern(
                engine.get_feedback(guess, answer)
            )
        if progress is not None:
            progress(guess_index + 1, len(guesses))
    return FeedbackPatternCache(
        guesses=tuple(guesses),
        answers=tuple(answers),
        matrix=matrix,
        guesses_sha256=word_list_fingerprint(guesses),
        answers_sha256=word_list_fingerprint(answers),
    )


def precomputed_feedback(
    guess: str,
    answer: str,
    *,
    cache: FeedbackPatternCache | None = None,
) -> FeedbackPattern:
    """Look up cached feedback. Raises if the pair is missing."""
    resolved = get_pattern_cache() if cache is None else cache
    if resolved is None:
        raise CacheError("feedback cache is not available")
    return resolved.feedback(guess, answer)


def lookup_feedback(
    guess: str,
    answer: str,
    *,
    cache: FeedbackPatternCache | None = None,
) -> FeedbackPattern:
    """Use the cache when possible; otherwise the reference feedback engine."""
    resolved = get_pattern_cache() if cache is None else cache
    if resolved is not None:
        try:
            return resolved.feedback(guess, answer)
        except CacheError:
            pass
    return get_feedback(guess, answer)
