"""Project paths and configuration."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
ANSWERS_PATH = DATA_DIR / "answers.txt"
ALLOWED_GUESSES_PATH = DATA_DIR / "allowed_guesses.txt"
CACHE_DIR = PROJECT_ROOT / "cache"
FEEDBACK_CACHE_PATH = CACHE_DIR / "feedback_patterns.npz"
DOCS_DIR = PROJECT_ROOT / "docs"
BENCHMARKS_DIR = PROJECT_ROOT / "benchmarks"
BENCHMARK_RESULTS_DIR = BENCHMARKS_DIR / "results"
BENCHMARK_FIGURES_DIR = BENCHMARKS_DIR / "figures"
OPENER_RESULTS_PATH = BENCHMARK_RESULTS_DIR / "opener_results.json"
MAX_GUESSES = 6
