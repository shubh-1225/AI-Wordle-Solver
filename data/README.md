# Word lists

These files are the original public Wordle dictionaries used as the solver's answer pool and allowed-guess vocabulary.

They are external data files. The application loads them at runtime and does not hard-code the word lists in Python.

## Files

| File | Role | Word count |
| --- | --- | ---: |
| `answers.txt` | Hidden-answer / candidate-answer pool | 2315 |
| `allowed_guesses.txt` | Every word a player may enter (includes all answers) | 12972 |

`allowed_guesses.txt` is the sorted union of the original answer list and the original extra-guess list.

## Source

Maintainer: [cfreshman](https://gist.github.com/cfreshman)

These gists extract the original Wordle source-code lists (pre–New York Times daily curation). They are the standard reproducible set used by many published solvers.

| List | Gist |
| --- | --- |
| Original answers, alphabetical | https://gist.github.com/cfreshman/a03ef2cba789d8cf00c08f767e0fad7b |
| Original extra guesses (not including answers) | https://gist.github.com/cfreshman/cdcdf777450c5b5301e439061d29694c |

Raw downloads used:

- https://gist.githubusercontent.com/cfreshman/a03ef2cba789d8cf00c08f767e0fad7b/raw/wordle-answers-alphabetical.txt
- https://gist.githubusercontent.com/cfreshman/cdcdf777450c5b5301e439061d29694c/raw

## Retrieval

- Retrieved: 2026-10-05
- Format: one lowercase 5-letter word per line, UTF-8, newline at end of file
- Answers unique: 2315
- Extra guesses unique: 10657
- Overlap between extra guesses and answers: 0
- Allowed guesses written: 2315 + 10657 = 12972
- Every answer is present in `allowed_guesses.txt`
- SHA-256 of `answers.txt` contents as loaded (newline-joined words): `5209b35f823f8b80f0404f863bd80df06d6a966c6eb1016d69f38badc6eed5d0`
- SHA-256 of `allowed_guesses.txt` contents as loaded: `498f38211e3bafbfd6cc824ed10537a974d502377aa92459d06ff6a5b6110bb8`

## Validation applied

- lowercase
- exactly 5 letters
- alphabetic ASCII characters only
- no duplicates
- answers ⊆ allowed guesses

## Limitations

- These are the **original Wordle** lists (~2,315 answers / ~12,972 valid guesses), not the live New York Times list.
- The New York Times has added, removed, and curated answers over time, so some current daily answers (for example later additions) are not in `answers.txt`.
- Extra guesses that NYT later added or removed are also not reflected here.
- The lists are third-party extracts of Wordle/NYT data. They are included for a student/local solver, with source attribution; they are not owned by this project.
- Because `allowed_guesses.txt` is larger than `answers.txt`, a valid typed guess is not always a possible hidden answer. That is intentional for information-gathering guesses.
