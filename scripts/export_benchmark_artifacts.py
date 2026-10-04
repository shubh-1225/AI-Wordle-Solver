"""Export published opener JSON to CSV tables and SVG figures."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.utils.config import (  # noqa: E402
    BENCHMARK_FIGURES_DIR,
    BENCHMARK_RESULTS_DIR,
    OPENER_RESULTS_PATH,
)


def load_results(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_starting_word_csv(payload: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "rank",
        "opener",
        "in_answer_list",
        "first_guess_entropy_bits",
        "games",
        "wins",
        "failed",
        "win_rate",
        "average_guesses",
        "median_guesses",
        "worst_case_guesses",
        "guesses_1",
        "guesses_2",
        "guesses_3",
        "guesses_4",
        "guesses_5",
        "guesses_6",
        "elapsed_seconds",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in payload["ranked_openers"]:
            dist = row["guess_distribution"]
            writer.writerow(
                {
                    "rank": row["rank"],
                    "opener": row["opener"],
                    "in_answer_list": row["in_answer_list"],
                    "first_guess_entropy_bits": f"{row['first_guess_entropy_bits']:.6f}",
                    "games": row["games"],
                    "wins": row["wins"],
                    "failed": row["failed"],
                    "win_rate": f"{row['win_rate']:.4f}",
                    "average_guesses": f"{row['average_guesses']:.6f}",
                    "median_guesses": row["median_guesses"],
                    "worst_case_guesses": row["worst_case_guesses"],
                    "guesses_1": dist.get("1", 0),
                    "guesses_2": dist.get("2", 0),
                    "guesses_3": dist.get("3", 0),
                    "guesses_4": dist.get("4", 0),
                    "guesses_5": dist.get("5", 0),
                    "guesses_6": dist.get("6", 0),
                    "elapsed_seconds": row["elapsed_seconds"],
                }
            )


def write_guess_distribution_csv(payload: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["opener", "guesses", "games"])
        for row in payload["ranked_openers"]:
            dist = row["guess_distribution"]
            for turn in range(1, 7):
                writer.writerow([row["opener"], turn, dist.get(str(turn), 0)])
            writer.writerow([row["opener"], "failed", row["failed"]])


def _svg_bar_chart(
    title: str,
    labels: list[str],
    values: list[float],
    ylabel: str,
    path: Path,
    *,
    y_min: float | None = None,
    y_max: float | None = None,
    value_format: str = "{:.3f}",
) -> None:
    width, height = 820, 420
    left, right, top, bottom = 70, 24, 48, 70
    plot_w = width - left - right
    plot_h = height - top - bottom
    lo = min(values) if y_min is None else y_min
    hi = max(values) if y_max is None else y_max
    span = hi - lo if hi != lo else 1.0
    bar_w = plot_w / max(len(values) * 1.6, 1)
    gap = bar_w * 0.6

    def y_pos(value: float) -> float:
        return top + plot_h - ((value - lo) / span) * plot_h

    bars = []
    for index, (label, value) in enumerate(zip(labels, values, strict=True)):
        x = left + gap + index * (bar_w + gap)
        y = y_pos(value)
        h = top + plot_h - y
        bars.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" '
            f'fill="#3B82F6"/>'
            f'<text x="{x + bar_w / 2:.1f}" y="{y - 8:.1f}" text-anchor="middle" '
            f'font-size="12" fill="#111827">{value_format.format(value)}</text>'
            f'<text x="{x + bar_w / 2:.1f}" y="{height - 36:.1f}" text-anchor="middle" '
            f'font-size="13" fill="#111827">{label}</text>'
        )

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="white"/>
  <text x="{width / 2:.1f}" y="28" text-anchor="middle" font-size="16" font-family="Segoe UI, Helvetica, Arial, sans-serif" fill="#111827">{title}</text>
  <line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#6B7280"/>
  <line x1="{left}" y1="{top + plot_h}" x2="{width - right}" y2="{top + plot_h}" stroke="#6B7280"/>
  <text x="18" y="{top + plot_h / 2:.1f}" transform="rotate(-90 18 {top + plot_h / 2:.1f})" text-anchor="middle" font-size="12" fill="#374151">{ylabel}</text>
  {"".join(bars)}
</svg>
'''
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")


def write_figures(payload: dict, figures_dir: Path) -> None:
    rows = payload["ranked_openers"]
    labels = [row["opener"] for row in rows]
    _svg_bar_chart(
        "Average guesses by starting word (maximum entropy, 2,315 answers)",
        labels,
        [row["average_guesses"] for row in rows],
        "Average guesses",
        figures_dir / "average_guesses_by_opener.svg",
        y_min=3.3,
        y_max=3.55,
        value_format="{:.3f}",
    )
    _svg_bar_chart(
        "First-guess Shannon entropy by starting word",
        labels,
        [row["first_guess_entropy_bits"] for row in rows],
        "Entropy (bits)",
        figures_dir / "opener_entropy.svg",
        y_min=5.84,
        y_max=5.90,
        value_format="{:.3f}",
    )
    soare = next(row for row in rows if row["opener"] == "soare")
    dist = soare["guess_distribution"]
    _svg_bar_chart(
        "Guess-count distribution for opener soare (maximum entropy)",
        ["2", "3", "4", "5", "6"],
        [dist.get(str(turn), 0) for turn in range(2, 7)],
        "Games (of 2,315)",
        figures_dir / "soare_guess_distribution.svg",
        y_min=0,
        value_format="{:.0f}",
    )


def main() -> None:
    source = OPENER_RESULTS_PATH
    if not source.is_file():
        raise SystemExit(f"Missing published results: {source}")
    payload = load_results(source)
    write_starting_word_csv(payload, BENCHMARK_RESULTS_DIR / "starting_word_results.csv")
    write_guess_distribution_csv(payload, BENCHMARK_RESULTS_DIR / "guess_distribution.csv")
    write_figures(payload, BENCHMARK_FIGURES_DIR)
    print(f"Exported tables to {BENCHMARK_RESULTS_DIR}")
    print(f"Exported figures to {BENCHMARK_FIGURES_DIR}")


if __name__ == "__main__":
    main()
