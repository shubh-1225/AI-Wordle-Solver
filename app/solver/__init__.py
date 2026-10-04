"""Solver engine package."""

from app.solver.cache import (
    CacheError,
    FeedbackPatternCache,
    get_pattern_cache,
    precomputed_feedback,
)
from app.solver.candidates import CandidateFilter, filter_candidates
from app.solver.constraints import (
    ContradictoryFeedbackError,
    ConstraintError,
)
from app.solver.entropy import calculate_entropy
from app.solver.feedback import FeedbackEngine, FeedbackError, get_feedback
from app.solver.ranking import get_best_guess, rank_guesses
from app.solver.simulator import WordleSimulator, rank_openers, simulate
from app.solver.solver import WordleSolver

__all__ = [
    "CacheError",
    "CandidateFilter",
    "ContradictoryFeedbackError",
    "ConstraintError",
    "FeedbackEngine",
    "FeedbackError",
    "FeedbackPatternCache",
    "WordleSimulator",
    "WordleSolver",
    "calculate_entropy",
    "filter_candidates",
    "get_best_guess",
    "get_feedback",
    "get_pattern_cache",
    "precomputed_feedback",
    "rank_openers",
    "rank_guesses",
    "simulate",
]
