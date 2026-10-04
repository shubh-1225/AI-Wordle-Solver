# Feedback pattern cache

The solver can precompute every allowed-guess × answer feedback pattern into
`cache/feedback_patterns.npz` (about 29 MiB, `uint8`, shape 12972 × 2315).

That file is **not** stored in git. Generate it locally:

```bash
python scripts/precompute_patterns.py
```

The application still works without the cache. Ranking is slower because it
falls back to the reference feedback engine.
