"""Benchmark the autonomous Wordle solver against answer words."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.models.statistics import BenchmarkSummary  # noqa: E402
from app.solver.simulator import WordleSimulator  # noqa: E402
from app.utils.word_utils import load_word_data  # noqa: E402


def _print_summary(summary: BenchmarkSummary, elapsed: float) -> None:
    print()
    print("SIMULATION RESULTS")
    print(f"Strategy: {summary.strategy}")
    print(f"Starting word: {summary.starting_word}")
    print(f"Games: {summary.games}")
    print(f"Elapsed: {elapsed:.1f}s")
    print(f"Win rate: {summary.win_rate:.4%}")
    print(f"Wins: {summary.wins}")
    print(f"Failed: {summary.failed}")
    print(f"Average guesses (wins): {summary.average_guesses:.4f}")
    print(f"Average guesses (failures count as 7): {summary.average_guesses_including_failures:.4f}")
    print(f"Median guesses (wins): {summary.median_guesses:.1f}")
    print(f"Minimum guesses: {summary.minimum_guesses}")
    print(f"Maximum guesses (wins): {summary.maximum_guesses}")
    print("Guess distribution:")
    for turn in range(1, 7):
        print(f"  {turn} guesses: {summary.guess_distribution[turn]}")
    print(f"  Failed: {summary.failed}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None, help="only the first N answers")
    parser.add_argument("--opener", default="soare", help="fixed first guess")
    parser.add_argument(
        "--strategy",
        default="maximum_entropy",
        choices=("maximum_entropy", "candidate_reduction"),
    )
    args = parser.parse_args()

    data = load_word_data()
    answers = data.answers if args.limit is None else data.answers[: args.limit]
    print(
        f"Benchmarking {len(answers)} answer(s) "
        f"strategy={args.strategy} opener={args.opener}"
    )
    simulator = WordleSimulator(data.answers, data.allowed_guesses, cache=True)
    started = time.perf_counter()
    last_report = started

    def progress(done: int, total: int, result: object) -> None:
        nonlocal last_report
        now = time.perf_counter()
        if done == total or done % 25 == 0 or now - last_report >= 10:
            elapsed = now - started
            rate = done / elapsed if elapsed else 0.0
            print(
                f"  {done}/{total} games ({rate:.2f} games/s, {elapsed:.1f}s)",
                flush=True,
            )
            last_report = now

    summary = simulator.benchmark(
        answers,
        strategy=args.strategy,
        starting_word=args.opener,
        progress=progress,
    )
    _print_summary(summary, time.perf_counter() - started)


if __name__ == "__main__":
    main()
