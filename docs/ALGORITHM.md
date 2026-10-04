# Algorithms

This document describes the algorithms that are actually implemented. There is no multi-ply lookahead and no learned policy.

## 1. Wordle feedback

Input: guess `g` and answer `a`, both length 5. Output: a 5-tuple with values `0` (gray), `1` (yellow), `2` (green).

**Pass 1 — greens.** For each index `i`, if `g[i] == a[i]`, mark green. Each green consumes that copy of the letter in the answer.

**Pass 2 — yellows.** For remaining guess letters, if an unused copy of that letter still exists in the answer, mark yellow and consume one copy. Otherwise gray.

```
function FEEDBACK(guess, answer):
    pattern ← [GRAY] * 5
    unused ← multiset of answer letters that are not green
    for i in 0..4:
        if guess[i] = answer[i]:
            pattern[i] ← GREEN
        else:
            unused.add(answer[i])
    for i in 0..4:
        if pattern[i] = GREEN: continue
        if unused.contains(guess[i]):
            pattern[i] ← YELLOW
            unused.remove(guess[i])
    return pattern
```

Both words are normalized to lowercase ASCII alphabetic length 5.

## 2. Duplicate-letter handling

Because yellows consume a remaining multiset, extra copies of a letter go gray. Examples the tests lock down include patterns for words such as `sassy` and `alloy`. Filtering never uses a simplified “letter is present” bitset; it always re-runs this coloring.

## 3. Constraint representation

History is a list of `GuessObservation(guess, feedback)`. The feasible set is:

```
C(history) = { a ∈ Answers | ∀ (g, p) ∈ history: FEEDBACK(g, a) = p }
```

That predicate **is** the constraint store. There is no separate interval or letter-count propagator, which avoids duplicate-letter bugs from ad-hoc rules.

The same guess with two different patterns raises `ContradictoryFeedbackError`.

## 4. Candidate filtering

`CandidateFilter` starts at the full answer tuple (2,315 words) and after each observation keeps only matching words, preserving order.

```
function APPLY(candidates, guess, pattern):
    return [a in candidates if FEEDBACK(guess, a) = pattern]
```

## 5. Entropy

Let `N = |C|`. A guess `g` induces counts `n_p = |{ a ∈ C | FEEDBACK(g, a) = p }|` over the 243 patterns.

```
H(g) = - Σ_{n_p > 0} (n_p / N) log2(n_p / N)
```

Uniform singleton partitions give the maximum `log2(N)` bits. A guess that always yields the same pattern has entropy 0.

## 6. Information gain and expected remaining

Under a uniform prior on remaining answers, expected remaining size after `g` is

```
E[|C'| | g] = Σ_p n_p² / N
```

Expected fractional reduction is `1 - E[|C'|]/N`. The GUI surfaces entropy, group count, remaining `N`, and that reduction.

## 7. Feedback pattern encoding

A pattern `(d0..d4)` with `d ∈ {0,1,2}` is stored as a base-3 integer

```
code = d0·3⁴ + d1·3³ + d2·3² + d3·3 + d4   ∈ {0, …, 242}
```

`uint8` is enough. Decoding recovers the five digits.

## 8. Precomputed feedback matrix

`scripts/precompute_patterns.py` builds a matrix `M` of shape

```
|allowed_guesses| × |answers| = 12972 × 2315
```

with `M[i, j] = encode(FEEDBACK(guess_i, answer_j))`. SHA-256 fingerprints of both word lists are stored in the `.npz` file. The solver loads the cache only when fingerprints match.

Ranking then takes the rows of selected guesses and the columns of remaining answers and uses `numpy.bincount` instead of Python loops.

Without the file, behavior is identical and slower.

## 9. Guess ranking

```
function RANK(guess_pool, C, objective):
    for g in unused(guess_pool):
        compute H(g) and E[|C'||g]
    if objective = entropy:
        sort by (-H, g not in C, g alphabetically)
    else:  # candidate_reduction
        sort by (E[|C'|], -H, g not in C, g alphabetically)
    return sorted list
```

`choose_guess` short-circuits when `|C| = 1`.

## 10. Search / lookahead

**Not implemented.** Autonomous play is greedy one-ply ranking for up to six turns. Opener evaluation is exhaustive over answers, not a deeper tree search.

## 11. Simulation

```
function SIMULATE(answer, strategy, opener):
    C ← Answers
    for turn in 1..6:
        g ← opener if turn = 1 and opener else RANK(pool, C, strategy)[0]
        p ← FEEDBACK(g, answer)
        C ← APPLY(C, g, p)
        if g = answer: return solved
    return failed
```

Failures contribute 7 toward `average_guesses_failures_as_7` in opener reports. The published maximum-entropy openers had zero failures.

Opener ranking key: average guesses with failures as 7, then win-only average, then win rate, then worst case, then opener spelling.
