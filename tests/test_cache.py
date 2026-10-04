"""Tests for precomputed base-3 feedback patterns."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from app.models.feedback import PATTERN_COUNT
from app.solver.cache import (
    CacheError,
    build_pattern_cache,
    decode_pattern,
    encode_pattern,
    load_pattern_cache_file,
    precomputed_feedback,
    save_pattern_cache,
)
from app.solver.entropy import calculate_entropy
from app.solver.feedback import get_feedback
from app.solver.ranking import rank_guesses


def test_encode_decode_roundtrip_all_243_patterns() -> None:
    for code in range(PATTERN_COUNT):
        pattern = decode_pattern(code)
        assert encode_pattern(pattern) == code
        assert all(value in (0, 1, 2) for value in pattern)


def test_encode_matches_positional_base3() -> None:
    assert encode_pattern((0, 0, 0, 0, 0)) == 0
    assert encode_pattern((2, 2, 2, 2, 2)) == PATTERN_COUNT - 1
    assert encode_pattern((1, 0, 2, 0, 1)) == ((1 * 81) + (0 * 27) + (2 * 9) + (0 * 3) + 1)


def test_tiny_cache_matches_reference_feedback(tmp_path: Path) -> None:
    guesses = ("house", "crane", "apple")
    answers = ("mouse", "house", "pleas")
    cache = build_pattern_cache(guesses, answers)
    for guess in guesses:
        for answer in answers:
            assert cache.feedback(guess, answer) == get_feedback(guess, answer)
            assert precomputed_feedback(guess, answer, cache=cache) == get_feedback(guess, answer)

    path = save_pattern_cache(cache, tmp_path / "feedback_patterns.npz")
    loaded = load_pattern_cache_file(path)
    assert loaded.matrix.shape == (3, 3)
    assert np.array_equal(loaded.matrix, cache.matrix)
    for guess in guesses:
        for answer in answers:
            assert loaded.feedback(guess, answer) == get_feedback(guess, answer)


def test_entropy_with_cache_matches_reference() -> None:
    guesses = ("abxxx", "axxxx", "abcdx")
    answers = ("aaaaa", "bbbbb", "ccccc", "ddddd")
    cache = build_pattern_cache(guesses, answers)
    for guess in guesses:
        cached = calculate_entropy(guess, answers, cache=cache)
        reference = calculate_entropy(guess, answers, cache=None)
        assert cached == pytest.approx(reference)


def test_ranking_with_cache_matches_reference() -> None:
    guesses = ("xxxxz", "abcdx", "aaaaa")
    answers = ("aaaaa", "bbbbb", "ccccc", "ddddd")
    cache = build_pattern_cache(guesses, answers)
    cached = rank_guesses(guesses, answers, cache=cache)
    reference = rank_guesses(guesses, answers, cache=None)
    assert [score.guess for score in cached] == [score.guess for score in reference]
    for left, right in zip(cached, reference, strict=True):
        assert left.entropy == pytest.approx(right.entropy)
        assert left.feedback_groups == right.feedback_groups
        assert left.in_candidate_set == right.in_candidate_set
        assert left.expected_remaining == pytest.approx(right.expected_remaining)


def test_missing_pair_falls_back_to_feedback_engine() -> None:
    cache = build_pattern_cache(("crane",), ("slate",))
    entropy = calculate_entropy("zzzzz", ["aaaaa"], cache=cache)
    assert entropy == calculate_entropy("zzzzz", ["aaaaa"], cache=None)


def test_precomputed_feedback_requires_cached_pair() -> None:
    cache = build_pattern_cache(("crane",), ("slate",))
    with pytest.raises(CacheError):
        precomputed_feedback("zzzzz", "slate", cache=cache)


def test_corrupt_cache_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "feedback_patterns.npz"
    path.write_bytes(b"not a numpy archive")
    with pytest.raises(CacheError, match="corrupt"):
        load_pattern_cache_file(path)


def test_project_cache_matches_reference_feedback() -> None:
    from app.utils.config import FEEDBACK_CACHE_PATH
    from app.utils.word_utils import load_word_data

    if not FEEDBACK_CACHE_PATH.is_file():
        pytest.skip("feedback cache has not been generated yet")

    data = load_word_data()
    cache = load_pattern_cache_file(FEEDBACK_CACHE_PATH)
    assert cache.matches_word_lists(data.allowed_guesses, data.answers)
    sample_guesses = data.allowed_guesses[:: max(1, len(data.allowed_guesses) // 40)][:40]
    sample_answers = data.answers[:: max(1, len(data.answers) // 40)][:40]
    for guess in sample_guesses:
        for answer in sample_answers:
            assert precomputed_feedback(guess, answer, cache=cache) == get_feedback(
                guess, answer
            )
    for guess in ("crane", "slate", "soare"):
        assert calculate_entropy(guess, data.answers, cache=cache) == pytest.approx(
            calculate_entropy(guess, data.answers, cache=None)
        )

