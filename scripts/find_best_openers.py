"""Rank selected starting words by full-game solver performance.

Results are computed from this project's answer list, allowed-guess list,
and deterministic entropy solver. They are not a universal ranking of
Wordle openers.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.models.statistics import OpenerReport  # noqa: E402
from app.solver.cache import word_list_fingerprint  # noqa: E402
from app.solver.constraints import ConstraintError  # noqa: E402
from app.solver.ranking import rank_guesses  # noqa: E402
from app.solver.simulator import WordleSimulator, rank_openers  # noqa: E402
from app.utils.config import OPENER_RESULTS_PATH  # noqa: E402
from app.utils.word_utils import load_word_data  # noqa: E402


def select_openers(
    allowed_guesses: tuple[str, ...],
    answers: tuple[str, ...],
    *,
    requested: tuple[str, ...],
    top_entropy: int,
    cache: object,
) -> list[str]:
    selected: list[str] = []
    seen: set[str] = set()

    def add(word: str) -> None:
        if word not in seen:
            selected.append(word)
            seen.add(word)

    if top_entropy:
        ranked = rank_guesses(
            allowed_guesses,
            answers,
            limit=top_entropy,
            cache=cache,
            objective="entropy",
        )
        for score in ranked:
            add(score.guess)

    for word in requested:
        if word not in allowed_guesses:
            raise ConstraintError(f"requested opener {word!r} is not in allowed_guesses")
        add(word)
    if not selected:
        raise ConstraintError("no starting words selected")
    return selected


def report_to_dict(report: OpenerReport, rank: int) -> dict[str, Any]:
    return {
        "rank": rank,
        "opener": report.opener,
        "in_answer_list": report.in_answer_list,
        "first_guess_entropy_bits": round(report.first_guess_entropy, 6),
        "games": report.games,
        "wins": report.wins,
        "failed": report.failures,
        "win_rate": report.win_rate,
        "average_guesses": report.average_guesses,
        "median_guesses": report.median_guesses,
        "minimum_guesses": report.minimum_guesses,
        "worst_case_guesses": report.maximum_guesses,
        "average_guesses_failures_as_7": report.average_guesses_including_failures,
        "guess_distribution": {str(turn): count for turn, count in report.guess_distribution.items()},
        "worst_case_answers": list(report.worst_case_answers),
        "failed_answers": list(report.failed_answers),
        "elapsed_seconds": round(report.elapsed_seconds, 3),
    }


def save_results(payload: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--openers",
        default="",
        help="comma-separated extra starting words to include",
    )
    parser.add_argument(
        "--top-entropy",
        type=int,
        default=5,
        help="include the N highest first-guess-entropy allowed words (0 to disable)",
    )
    parser.add_argument(
        "--strategy",
        default="maximum_entropy",
        choices=("maximum_entropy", "candidate_reduction"),
    )
    parser.add_argument(
        "--output",
        default=str(OPENER_RESULTS_PATH),
        help="JSON output path",
    )
    args = parser.parse_args()

    data = load_word_data()
    simulator = WordleSimulator(data.answers, data.allowed_guesses, cache=True)
    requested = tuple(
        word.strip().lower() for word in args.openers.split(",") if word.strip()
    )
    openers = select_openers(
        data.allowed_guesses,
        data.answers,
        requested=requested,
        top_entropy=args.top_entropy,
        cache=simulator.solver.pattern_cache,
    )
    print(
        f"Evaluating {len(openers)} opener(s) on {len(data.answers)} answers "
        f"with strategy={args.strategy}"
    )
    print("Selected starting words: " + ", ".join(openers))

    reports: list[OpenerReport] = []
    for index, opener in enumerate(openers, start=1):
        print(f"[{index}/{len(openers)}] simulating opener {opener!r}...", flush=True)
        report = simulator.benchmark_opener(opener, strategy=args.strategy)
        reports.append(report)
        print(
            f"    avg={report.average_guesses:.4f} "
            f"median={report.median_guesses:.1f} "
            f"worst={report.maximum_guesses} "
            f"win_rate={report.win_rate:.4%} "
            f"({report.elapsed_seconds:.1f}s)",
            flush=True,
        )

    ranked = rank_openers(reports)
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "methodology": (
            "Each selected starting word is played as guess 1 against every "
            "answer in data/answers.txt. Later guesses are chosen by the "
            "named deterministic strategy using data/allowed_guesses.txt and "
            "the precomputed feedback cache when available. Rankings apply "
            "only to these lists and this solver; they are not a universal "
            "optimum."
        ),
        "strategy": args.strategy,
        "answer_count": len(data.answers),
        "allowed_guess_count": len(data.allowed_guesses),
        "answers_sha256": word_list_fingerprint(data.answers),
        "allowed_guesses_sha256": word_list_fingerprint(data.allowed_guesses),
        "selected_openers": openers,
        "ranking_key": [
            "average_guesses_failures_as_7",
            "average_guesses",
            "win_rate descending",
            "worst_case_guesses",
            "opener alphabetical",
        ],
        "ranked_openers": [report_to_dict(report, rank) for rank, report in enumerate(ranked, start=1)],
    }
    output = save_results(payload, Path(args.output))
    print()
    print("RANKED STARTING WORDS (this dictionary and solver only)")
    for row in payload["ranked_openers"]:
        print(
            f"  {row['rank']}. {row['opener']}  "
            f"avg={row['average_guesses']:.4f}  "
            f"median={row['median_guesses']:.1f}  "
            f"worst={row['worst_case_guesses']}  "
            f"win={row['win_rate']:.2%}"
        )
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
