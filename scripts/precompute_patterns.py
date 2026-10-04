"""Generate cache/feedback_patterns.npz from the project word lists."""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.solver.cache import build_pattern_cache, save_pattern_cache  # noqa: E402
from app.utils.config import FEEDBACK_CACHE_PATH  # noqa: E402
from app.utils.word_utils import load_word_data  # noqa: E402


def main() -> None:
    data = load_word_data()
    guesses = data.allowed_guesses
    answers = data.answers
    print(f"Building feedback matrix: {len(guesses)} guesses x {len(answers)} answers")
    started = time.perf_counter()
    last_report = started

    def progress(done: int, total: int) -> None:
        nonlocal last_report
        now = time.perf_counter()
        if done == total or now - last_report >= 5 or done % 500 == 0:
            elapsed = now - started
            rate = done / elapsed if elapsed else 0.0
            print(f"  {done}/{total} guesses ({rate:.1f} guesses/s, {elapsed:.1f}s)", flush=True)
            last_report = now

    cache = build_pattern_cache(guesses, answers, progress=progress)
    path = save_pattern_cache(cache, FEEDBACK_CACHE_PATH)
    elapsed = time.perf_counter() - started
    size_mb = path.stat().st_size / (1024 * 1024)
    memory_mb = cache.matrix.nbytes / (1024 * 1024)
    print(f"Wrote {path}")
    print(f"Matrix memory: {memory_mb:.2f} MiB")
    print(f"File size: {size_mb:.2f} MiB")
    print(f"Elapsed: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
