"""Shannon entropy of a Wordle guess against remaining candidates."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Sequence
from math import log2

import numpy as np

from app.models.feedback import PATTERN_COUNT, FeedbackPattern
from app.solver.cache import FeedbackPatternCache, decode_pattern, get_pattern_cache
from app.solver.constraints import ConstraintError
from app.solver.feedback import get_feedback

_UNSET = object()


def _resolve_cache(cache: object) -> FeedbackPatternCache | None:
    if cache is _UNSET:
        return get_pattern_cache()
    return cache  # type: ignore[return-value]


def partition_candidates(
    guess: str,
    candidates: Sequence[str],
    *,
    cache: FeedbackPatternCache | None | object = _UNSET,
) -> dict[FeedbackPattern, tuple[str, ...]]:
    """Group candidate answers by the feedback they would produce."""
    if not candidates:
        raise ConstraintError("candidates must not be empty")

    resolved = _resolve_cache(cache)
    groups: dict[FeedbackPattern, list[str]] = defaultdict(list)
    encoded = resolved.encoded_row(guess, candidates) if resolved is not None else None
    if encoded is not None:
        for answer, code in zip(candidates, encoded, strict=True):
            groups[decode_pattern(int(code))].append(answer)
        return {pattern: tuple(words) for pattern, words in groups.items()}

    for answer in candidates:
        groups[get_feedback(guess, answer)].append(answer)
    return {pattern: tuple(words) for pattern, words in groups.items()}


def pattern_counts(
    guess: str,
    candidates: Sequence[str],
    *,
    cache: FeedbackPatternCache | None | object = _UNSET,
) -> Counter[FeedbackPattern]:
    if not candidates:
        raise ConstraintError("candidates must not be empty")

    resolved = _resolve_cache(cache)
    counts: Counter[FeedbackPattern] = Counter()
    encoded = resolved.encoded_row(guess, candidates) if resolved is not None else None
    if encoded is not None:
        for code in encoded.tolist():
            counts[decode_pattern(int(code))] += 1
        return counts

    for answer in candidates:
        counts[get_feedback(guess, answer)] += 1
    return counts


def entropy_from_counts(counts: Counter[FeedbackPattern], total: int) -> float:
    entropy = 0.0
    for count in counts.values():
        probability = count / total
        entropy -= probability * log2(probability)
    return entropy


def entropy_from_encoded_patterns(codes: np.ndarray, total: int) -> float:
    counts = np.bincount(np.asarray(codes, dtype=np.int32), minlength=PATTERN_COUNT)
    entropy = 0.0
    for count in counts:
        if count:
            probability = int(count) / total
            entropy -= probability * log2(probability)
    return entropy


def calculate_entropy(
    guess: str,
    candidates: Sequence[str],
    *,
    cache: FeedbackPatternCache | None | object = _UNSET,
) -> float:
    """Return H(g) = -Σ p_i log2(p_i) for guess g against candidate answers."""
    if not candidates:
        raise ConstraintError("candidates must not be empty")
    resolved = _resolve_cache(cache)
    encoded = resolved.encoded_row(guess, candidates) if resolved is not None else None
    if encoded is not None:
        return entropy_from_encoded_patterns(encoded, len(candidates))
    counts = pattern_counts(guess, candidates, cache=None)
    return entropy_from_counts(counts, len(candidates))


def expected_remaining(
    guess: str,
    candidates: Sequence[str],
    *,
    cache: FeedbackPatternCache | None | object = _UNSET,
) -> float:
    """Expected number of candidates remaining after playing `guess`."""
    if not candidates:
        raise ConstraintError("candidates must not be empty")
    resolved = _resolve_cache(cache)
    encoded = resolved.encoded_row(guess, candidates) if resolved is not None else None
    if encoded is not None:
        counts = np.bincount(np.asarray(encoded, dtype=np.int32), minlength=PATTERN_COUNT)
        return float(np.dot(counts, counts) / len(candidates))
    counts = pattern_counts(guess, candidates, cache=None)
    total = len(candidates)
    return sum(count * count for count in counts.values()) / total
