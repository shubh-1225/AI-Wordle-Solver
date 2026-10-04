"""Rank allowed guesses by expected information gain."""

from __future__ import annotations

from collections.abc import Sequence
from math import log2

import numpy as np

from app.models.feedback import PATTERN_COUNT
from app.models.recommendation import GuessScore, Recommendation
from app.solver.cache import FeedbackPatternCache, get_pattern_cache
from app.solver.constraints import ConstraintError
from app.solver.entropy import entropy_from_counts, pattern_counts

_UNSET = object()
PATTERN_SPACE = PATTERN_COUNT


def _resolve_cache(cache: object) -> FeedbackPatternCache | None:
    if cache is _UNSET:
        return get_pattern_cache()
    return cache  # type: ignore[return-value]


def _score_from_bincount(
    guess: str,
    counts: np.ndarray,
    total: int,
    candidate_set: set[str],
) -> GuessScore:
    entropy = 0.0
    groups = 0
    squares = 0
    for count in counts:
        value = int(count)
        if not value:
            continue
        groups += 1
        squares += value * value
        probability = value / total
        entropy -= probability * log2(probability)
    return GuessScore(
        guess=guess,
        entropy=entropy,
        feedback_groups=groups,
        in_candidate_set=guess in candidate_set,
        expected_remaining=squares / total,
    )


def score_guess(
    guess: str,
    candidates: Sequence[str],
    *,
    candidate_set: set[str] | None = None,
    cache: FeedbackPatternCache | None | object = _UNSET,
) -> GuessScore:
    if not candidates:
        raise ConstraintError("candidates must not be empty")
    answers = candidate_set if candidate_set is not None else set(candidates)
    resolved = _resolve_cache(cache)
    encoded = resolved.encoded_row(guess, candidates) if resolved is not None else None
    if encoded is not None:
        counts = np.bincount(np.asarray(encoded, dtype=np.int32), minlength=PATTERN_SPACE)
        return _score_from_bincount(guess, counts, len(candidates), answers)

    counts = pattern_counts(guess, candidates, cache=None)
    total = len(candidates)
    return GuessScore(
        guess=guess,
        entropy=entropy_from_counts(counts, total),
        feedback_groups=len(counts),
        in_candidate_set=guess in answers,
        expected_remaining=sum(count * count for count in counts.values()) / total,
    )


def rank_guesses(
    guesses: Sequence[str],
    candidates: Sequence[str],
    *,
    limit: int | None = None,
    cache: FeedbackPatternCache | None | object = _UNSET,
    objective: str = "entropy",
) -> tuple[GuessScore, ...]:
    """Rank guesses by entropy, then prefer remaining answers, then A–Z."""
    if not candidates:
        raise ConstraintError("candidates must not be empty")
    if not guesses:
        raise ConstraintError("guess pool must not be empty")
    if objective not in {"entropy", "expected_remaining"}:
        raise ConstraintError(f"unknown ranking objective {objective!r}")

    candidate_set = set(candidates)
    resolved = _resolve_cache(cache)
    ranked: list[GuessScore] = []

    columns = resolved.candidate_columns(candidates) if resolved is not None else None
    if columns is not None and resolved is not None:
        cached_rows: list[tuple[str, int]] = []
        uncached: list[str] = []
        for guess in guesses:
            row = resolved.guess_index(guess)
            if row is None:
                uncached.append(guess)
            else:
                cached_rows.append((guess, row))

        if cached_rows:
            row_indices = np.fromiter(
                (row for _, row in cached_rows),
                dtype=np.int32,
                count=len(cached_rows),
            )
            submatrix = resolved.matrix[np.ix_(row_indices, columns)]
            total = len(candidates)
            for (guess, _), codes in zip(cached_rows, submatrix, strict=True):
                counts = np.bincount(codes.astype(np.int32, copy=False), minlength=PATTERN_SPACE)
                ranked.append(_score_from_bincount(guess, counts, total, candidate_set))

        for guess in uncached:
            ranked.append(score_guess(guess, candidates, candidate_set=candidate_set, cache=None))
    else:
        ranked = [
            score_guess(guess, candidates, candidate_set=candidate_set, cache=None)
            for guess in guesses
        ]

    if objective == "entropy":
        ranked.sort(key=lambda score: (-score.entropy, not score.in_candidate_set, score.guess))
    else:
        ranked.sort(
            key=lambda score: (
                score.expected_remaining,
                -score.entropy,
                not score.in_candidate_set,
                score.guess,
            )
        )
    if limit is not None:
        ranked = ranked[:limit]
    return tuple(ranked)


def get_best_guess(
    guesses: Sequence[str],
    candidates: Sequence[str],
    *,
    cache: FeedbackPatternCache | None | object = _UNSET,
    objective: str = "entropy",
) -> GuessScore:
    return rank_guesses(guesses, candidates, limit=1, cache=cache, objective=objective)[0]


def recommendation_from_scores(
    scores: Sequence[GuessScore],
    remaining_candidates: int,
) -> Recommendation:
    if not scores:
        raise ConstraintError("no guesses were ranked")
    best = scores[0]
    return Recommendation(
        best_guess=best.guess,
        entropy=best.entropy,
        feedback_groups=best.feedback_groups,
        remaining_candidates=remaining_candidates,
        expected_remaining=best.expected_remaining,
        expected_reduction=(
            1.0 - (best.expected_remaining / remaining_candidates)
            if remaining_candidates
            else 0.0
        ),
        ranked_guesses=tuple(scores),
    )
