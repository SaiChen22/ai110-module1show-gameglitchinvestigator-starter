# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Streamlit app
python -m streamlit run app.py

# Run all tests
pytest

# Run a single test
pytest tests/test_game_logic.py::test_winning_guess
```

A `.venv` directory exists in the repo root; activate it with `source .venv/bin/activate` if needed.

## Architecture

This is a CodePath educational exercise: a deliberately buggy Streamlit number-guessing game that students must debug and fix.

**`app.py`** — Streamlit UI layer. Manages `st.session_state` for `secret`, `attempts`, `score`, `status`, and `history`. Imports all game logic from `logic_utils`. Contains an intentional bug on lines 97-100 where `secret` is cast to `str` on even attempts, corrupting type-based comparisons in `check_guess`.

**`logic_utils.py`** — Pure functions with no Streamlit dependency:
- `get_range_for_difficulty(difficulty)` — returns `(low, high)` for Easy/Normal/Hard
- `parse_guess(raw)` — validates and parses user input to `(ok, int|None, error|None)`
- `check_guess(guess, secret)` — returns `(outcome, message)` tuple; hints are intentionally inverted ("Too High" says "Go HIGHER")
- `update_score(current_score, outcome, attempt_number)` — scoring logic with an off-by-one bug

**`tests/test_game_logic.py`** — pytest tests for `check_guess`. Note: tests assert on just the outcome string (e.g., `"Win"`), but `check_guess` currently returns a `(outcome, message)` tuple — this mismatch is part of the exercise to fix.

## Known Intentional Bugs (the assignment)

1. **Inverted hints** in `check_guess`: "Too High" emits "Go HIGHER" and "Too Low" emits "Go LOWER"
2. **Type corruption** in `app.py`: `secret` is coerced to `str` on every even attempt, breaking numeric comparison
3. **Test/API mismatch**: tests expect `check_guess` to return a plain string, but it returns a tuple
4. **Score bug** in `update_score`: uses `attempt_number + 1` instead of `attempt_number` in the win calculation
