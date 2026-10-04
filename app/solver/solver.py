"""Entropy-based Wordle solver. Independent of the GUI."""

from __future__ import annotations

from collections.abc import Sequence

from app.models.recommendation import GuessScore, Recommendation
from app.solver.cache import FeedbackPatternCache, get_pattern_cache
from app.solver.candidates import CandidateFilter
from app.solver.entropy import calculate_entropy
from app.solver.ranking import get_best_guess, rank_guesses, recommendation_from_scores


class WordleSolver:
    """Track candidates and rank guesses by Shannon entropy."""

    def __init__(
        self,
        answers: Sequence[str],
        allowed_guesses: Sequence[str] | None = None,
        *,
        cache: FeedbackPatternCache | None | bool = True,
    ) -> None:
        self._filter = CandidateFilter(answers)
        self._allowed_guesses = tuple(allowed_guesses) if allowed_guesses is not None else tuple(answers)
        if cache is True:
            loaded = get_pattern_cache()
            if loaded is not None and loaded.matches_word_lists(
                guesses=self._allowed_guesses,
                answers=self._filter.answers,
            ):
                self._cache = loaded
            else:
                self._cache = None
        elif cache is False:
            self._cache = None
        else:
            self._cache = cache

    @property
    def answers(self) -> tuple[str, ...]:
        return self._filter.answers

    @property
    def allowed_guesses(self) -> tuple[str, ...]:
        return self._allowed_guesses

    @property
    def pattern_cache(self) -> FeedbackPatternCache | None:
        return self._cache

    def reset(self) -> tuple[str, ...]:
        return self._filter.reset()

    def update(self, guess: str, feedback: Sequence[int]) -> tuple[str, ...]:
        return self._filter.apply(guess, feedback)

    def get_candidates(self) -> tuple[str, ...]:
        return self._filter.candidates

    def get_entropy(self, guess: str) -> float:
        return calculate_entropy(guess, self.get_candidates(), cache=self._cache)

    def get_ranked_guesses(
        self,
        limit: int = 5,
        *,
        guesses: Sequence[str] | None = None,
    ) -> tuple[GuessScore, ...]:
        pool = self._allowed_guesses if guesses is None else guesses
        return rank_guesses(pool, self.get_candidates(), limit=limit, cache=self._cache)

    def get_best_guess(self, *, guesses: Sequence[str] | None = None) -> GuessScore:
        pool = self._allowed_guesses if guesses is None else guesses
        return get_best_guess(pool, self.get_candidates(), cache=self._cache)

    def get_recommendation(
        self,
        limit: int = 5,
        *,
        guesses: Sequence[str] | None = None,
    ) -> Recommendation:
        scores = self.get_ranked_guesses(limit=limit, guesses=guesses)
        return recommendation_from_scores(scores, remaining_candidates=len(self.get_candidates()))
