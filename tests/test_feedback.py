"""Tests for the Wordle feedback engine, including duplicate-letter cases."""

from __future__ import annotations

import pytest

from app.models.feedback import GRAY, GREEN, YELLOW
from app.solver.feedback import FeedbackEngine, FeedbackError, get_feedback


def test_mouse_vs_house_mixed_green_and_gray() -> None:
    assert get_feedback("mouse", "house") == (GRAY, GREEN, GREEN, GREEN, GREEN)


def test_all_green_identical_words() -> None:
    assert get_feedback("crane", "crane") == (GREEN, GREEN, GREEN, GREEN, GREEN)


def test_all_gray_no_shared_letters() -> None:
    assert get_feedback("glyph", "crane") == (GRAY, GRAY, GRAY, GRAY, GRAY)


def test_mixed_feedback_weary_vs_crane() -> None:
    assert get_feedback("weary", "crane") == (GRAY, YELLOW, GREEN, YELLOW, GRAY)


def test_feedback_engine_class_matches_module_function() -> None:
    engine = FeedbackEngine()
    assert engine.get_feedback("slate", "crane") == get_feedback("slate", "crane")


def test_normalizes_case() -> None:
    assert get_feedback("CRANE", "crane") == (GREEN, GREEN, GREEN, GREEN, GREEN)
    assert get_feedback("Mouse", "HOUSE") == (GRAY, GREEN, GREEN, GREEN, GREEN)


def test_speed_vs_erase_duplicate_e_both_yellow() -> None:
    # ERASE has two E's; SPEED has two unmatched E's so both can be yellow.
    assert get_feedback("speed", "erase") == (YELLOW, GRAY, YELLOW, YELLOW, GRAY)


def test_geese_vs_great_green_plus_duplicate_gray() -> None:
    # GREAT has one E, already used as green at position 3; extra E's are gray.
    assert get_feedback("geese", "great") == (GREEN, GRAY, GREEN, GRAY, GRAY)


def test_cheer_vs_crepe_green_plus_yellow_remaining_e() -> None:
    # CREPE has two E's: one green at position 3, one leftover for the other E.
    assert get_feedback("cheer", "crepe") == (GREEN, GRAY, GREEN, YELLOW, YELLOW)


def test_mamma_vs_charm_yellow_plus_duplicate_gray() -> None:
    # CHARM has one M and one A; extra copies in MAMMA are gray.
    assert get_feedback("mamma", "charm") == (YELLOW, YELLOW, GRAY, GRAY, GRAY)


def test_aaaaa_vs_abbbb_only_first_a_green() -> None:
    assert get_feedback("aaaaa", "abbbb") == (GREEN, GRAY, GRAY, GRAY, GRAY)


def test_aaaaa_vs_babaa_extra_as_gray_after_greens() -> None:
    assert get_feedback("aaaaa", "babaa") == (GRAY, GREEN, GRAY, GREEN, GREEN)


def test_apple_vs_pleas_second_p_gray() -> None:
    # PLEAS has one P; APPLE's second P is gray after the first is yellow.
    assert get_feedback("apple", "pleas") == (YELLOW, YELLOW, GRAY, YELLOW, YELLOW)


def test_pleas_vs_apple_both_ps_available_in_answer() -> None:
    assert get_feedback("pleas", "apple") == (YELLOW, YELLOW, YELLOW, YELLOW, GRAY)


def test_balls_vs_llama_two_yellow_ls() -> None:
    assert get_feedback("balls", "llama") == (GRAY, YELLOW, YELLOW, YELLOW, GRAY)


def test_llama_vs_balls_third_a_gray() -> None:
    assert get_feedback("llama", "balls") == (YELLOW, YELLOW, YELLOW, GRAY, GRAY)


def test_robot_vs_tooth_green_o_then_yellow_o() -> None:
    assert get_feedback("robot", "tooth") == (GRAY, GREEN, GRAY, YELLOW, YELLOW)


def test_tooth_vs_robot_second_t_gray() -> None:
    # ROBOT has one T, consumed as yellow by the first T.
    assert get_feedback("tooth", "robot") == (YELLOW, GREEN, YELLOW, GRAY, GRAY)


def test_sassy_vs_guess_yellow_s_then_gray_extra_s() -> None:
    # GUESS has two S's. One is green at position 4; one remaining S makes
    # the first guess S yellow; the leftover S in SASSY is gray.
    assert get_feedback("sassy", "guess") == (YELLOW, GRAY, GRAY, GREEN, GRAY)


def test_guess_vs_sassy_both_s_yellow_or_green_correctly() -> None:
    # SASSY: S A S S Y
    # GUESS: G U E S S
    # position 4 S vs Y no; remaining S,A,S,S after no greens? pos3 S vs S green.
    assert get_feedback("guess", "sassy") == (GRAY, GRAY, GRAY, GREEN, YELLOW)


def test_yellow_does_not_reuse_green_letter() -> None:
    assert get_feedback("eerie", "there") == (YELLOW, GRAY, YELLOW, GRAY, GREEN)


def test_repeated_same_guess_and_answer_are_deterministic() -> None:
    first = get_feedback("alloy", "llama")
    second = get_feedback("alloy", "llama")
    assert first == second == (YELLOW, GREEN, YELLOW, GRAY, GRAY)


def test_rejects_wrong_length() -> None:
    with pytest.raises(FeedbackError, match="exactly 5 letters"):
        get_feedback("cranes", "crane")
    with pytest.raises(FeedbackError, match="exactly 5 letters"):
        get_feedback("crane", "to")


def test_rejects_non_alphabetic() -> None:
    with pytest.raises(FeedbackError, match="alphabetic"):
        get_feedback("cra1e", "crane")
    with pytest.raises(FeedbackError, match="alphabetic"):
        get_feedback("crane", "cra_e")


def test_rejects_empty() -> None:
    with pytest.raises(FeedbackError):
        get_feedback("", "crane")
