"""Tests for Shannon entropy of Wordle guesses."""

from __future__ import annotations

from math import log2

import pytest

from app.solver.constraints import ConstraintError
from app.solver.entropy import calculate_entropy, partition_candidates, pattern_counts


def test_single_candidate_has_zero_entropy() -> None:
    assert calculate_entropy("aaaaa", ["aaaaa"]) == 0.0
    assert calculate_entropy("bbbbb", ["aaaaa"]) == 0.0


def test_two_equal_groups_have_one_bit() -> None:
    candidates = ["aaaaa", "bbbbb"]
    entropy = calculate_entropy("abxxx", candidates)
    groups = partition_candidates("abxxx", candidates)
    assert len(groups) == 2
    assert all(len(words) == 1 for words in groups.values())
    assert entropy == pytest.approx(1.0)


def test_four_equal_groups_have_two_bits() -> None:
    # "abcdx" produces a unique green position against each of a/b/c/d.
    candidates = ["aaaaa", "bbbbb", "ccccc", "ddddd"]
    entropy = calculate_entropy("abcdx", candidates)
    groups = partition_candidates("abcdx", candidates)
    assert len(groups) == 4
    assert entropy == pytest.approx(2.0)


def test_two_and_one_partition_matches_hand_calculation() -> None:
    candidates = ["aaaaa", "bbbbb", "ccccc"]
    entropy = calculate_entropy("abxxx", candidates)
    counts = pattern_counts("abxxx", candidates)
    assert sorted(counts.values()) == [1, 1, 1]
    expected = -(
        (1 / 3) * log2(1 / 3)
        + (1 / 3) * log2(1 / 3)
        + (1 / 3) * log2(1 / 3)
    )
    assert entropy == pytest.approx(expected)
    assert entropy == pytest.approx(log2(3))


def test_unbalanced_two_one_split() -> None:
    # "axxxx" greens only against aaaaa; bbbbb and ccccc both yield all-gray.
    candidates = ["aaaaa", "bbbbb", "ccccc"]
    entropy = calculate_entropy("axxxx", candidates)
    counts = pattern_counts("axxxx", candidates)
    assert sorted(counts.values()) == [1, 2]
    expected = -((1 / 3) * log2(1 / 3) + (2 / 3) * log2(2 / 3))
    assert entropy == pytest.approx(expected)
    assert entropy == pytest.approx(0.9182958340544894)


def test_identical_candidates_have_zero_entropy() -> None:
    candidates = ["crane", "crane"]
    assert calculate_entropy("slate", candidates) == 0.0


def test_empty_candidates_raise() -> None:
    with pytest.raises(ConstraintError, match="empty"):
        calculate_entropy("crane", [])
