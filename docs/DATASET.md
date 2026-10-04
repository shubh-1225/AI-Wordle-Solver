# Dataset

## Vocabularies

| File | Role | Count |
| --- | --- | ---: |
| `data/answers.txt` | Hidden-answer / candidate-answer pool | 2,315 |
| `data/allowed_guesses.txt` | Every word the player/solver may type | 12,972 |

`allowed_guesses.txt` is the sorted union of the original answer list and the original extra-guess list. Every answer is a valid guess. Many valid guesses are **not** possible hidden answers; those words exist for information-gathering probes (`soare`, `reast`, `roate`, `raile`).

## Why two lists

Wordle accepts a large allowed-guess dictionary but samples the daily answer from a smaller list. An entropy solver that could only guess remaining answers would miss high-information probes. Ranking therefore scores the **allowed** list against the **answer** list as the prior.

## Source

Maintainer: [cfreshman](https://gist.github.com/cfreshman). The gists extract the original Wordle source-code lists (before New York Times daily curation). They are the usual reproducible baseline in published solver write-ups.

| List | Gist |
| --- | --- |
| Answers, alphabetical | https://gist.github.com/cfreshman/a03ef2cba789d8cf00c08f767e0fad7b |
| Extra guesses (excluding answers) | https://gist.github.com/cfreshman/cdcdf777450c5b5301e439061d29694c |

Raw URLs used on retrieval:

- https://gist.githubusercontent.com/cfreshman/a03ef2cba789d8cf00c08f767e0fad7b/raw/wordle-answers-alphabetical.txt
- https://gist.githubusercontent.com/cfreshman/cdcdf777450c5b5301e439061d29694c/raw

Retrieved: **2026-10-05**.

## Validation (enforced at load time)

`app/utils/word_utils.py` and `tests/test_word_data.py` require:

- lowercase
- exactly five letters
- ASCII alphabetic characters
- no duplicates
- answers ⊆ allowed guesses

SHA-256 fingerprints recorded with the published opener run:

- answers: `5209b35f823f8b80f0404f863bd80df06d6a966c6eb1016d69f38badc6eed5d0`
- allowed guesses: `498f38211e3bafbfd6cc824ed10537a974d502377aa92459d06ff6a5b6110bb8`

## Licensing / usage

These files are third-party extracts of Wordle vocabulary, not original work of this repository. They are bundled for a local, educational solver with attribution. This project does not claim NYT or Josh Wardle ownership, and the MIT license on the source code does not purport to license the word lists as the author’s data.

If you cannot redistribute the lists in a derived project, omit `data/*.txt` and restore them from the gist URLs above, then re-run `python scripts/precompute_patterns.py`.

## Limitations

- Original Wordle lists, **not** the current New York Times list.
- NYT has added, removed, and curated answers; some later dailies are absent.
- Changing either file invalidates the cache fingerprints and the opener ranking.
