"""Tests for the external Wordle word-data layer."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.utils.config import ALLOWED_GUESSES_PATH, ANSWERS_PATH
from app.utils.word_utils import WordListError, load_word_data, load_word_file


def _write_list(path: Path, words: list[str]) -> Path:
    path.write_text("\n".join(words) + "\n", encoding="utf-8")
    return path


def test_project_word_files_exist() -> None:
    assert ANSWERS_PATH.is_file()
    assert ALLOWED_GUESSES_PATH.is_file()


def test_load_project_word_data() -> None:
    data = load_word_data()
    assert len(data.answers) == 2315
    assert len(data.allowed_guesses) == 12972
    assert set(data.answers).issubset(set(data.allowed_guesses))


def test_project_lists_are_lowercase_five_letter_alpha() -> None:
    data = load_word_data()
    for word in (*data.answers, *data.allowed_guesses):
        assert word == word.lower()
        assert len(word) == 5
        assert word.isascii() and word.isalpha()


def test_project_lists_have_no_duplicates() -> None:
    data = load_word_data()
    assert len(data.answers) == len(set(data.answers))
    assert len(data.allowed_guesses) == len(set(data.allowed_guesses))


def test_load_word_file_rejects_uppercase(tmp_path: Path) -> None:
    path = _write_list(tmp_path / "words.txt", ["crane"])
    path.write_text("CRANE\n", encoding="utf-8")
    with pytest.raises(WordListError, match="lowercase"):
        load_word_file(path, label="answers")


def test_load_word_file_rejects_wrong_length(tmp_path: Path) -> None:
    path = _write_list(tmp_path / "words.txt", ["cranes"])
    with pytest.raises(WordListError, match="exactly 5 letters"):
        load_word_file(path, label="answers")


def test_load_word_file_rejects_non_alpha(tmp_path: Path) -> None:
    path = _write_list(tmp_path / "words.txt", ["cra1e"])
    with pytest.raises(WordListError, match="alphabetic"):
        load_word_file(path, label="answers")


def test_load_word_file_rejects_duplicates(tmp_path: Path) -> None:
    path = _write_list(tmp_path / "words.txt", ["crane", "slate", "crane"])
    with pytest.raises(WordListError, match="duplicate"):
        load_word_file(path, label="answers")


def test_load_word_data_rejects_missing_file(tmp_path: Path) -> None:
    answers = _write_list(tmp_path / "answers.txt", ["crane"])
    with pytest.raises(WordListError, match="Missing"):
        load_word_data(answers, tmp_path / "missing.txt")


def test_load_word_data_requires_answers_in_allowed(tmp_path: Path) -> None:
    answers = _write_list(tmp_path / "answers.txt", ["crane", "slate"])
    allowed = _write_list(tmp_path / "allowed.txt", ["crane", "aahed"])
    with pytest.raises(WordListError, match="allowed_guesses"):
        load_word_data(answers, allowed)


def test_load_word_data_accepts_valid_lists(tmp_path: Path) -> None:
    answers = _write_list(tmp_path / "answers.txt", ["crane", "slate"])
    allowed = _write_list(tmp_path / "allowed.txt", ["aahed", "crane", "slate"])
    data = load_word_data(answers, allowed)
    assert data.answers == ("crane", "slate")
    assert data.allowed_guesses == ("aahed", "crane", "slate")
