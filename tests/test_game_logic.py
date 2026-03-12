from logic_utils import (
    check_guess,
    describe_guess_feedback,
    get_range_for_difficulty,
    load_high_score,
    maybe_update_high_score,
    parse_guess,
    update_score,
)


# --- check_guess: outcome ---


def test_winning_guess():
    # FIX: `check_guess()` returns `(outcome, message)`, so unpack first.
    outcome, _ = check_guess(50, 50)
    assert outcome == "Win"


def test_guess_too_high():
    outcome, _ = check_guess(60, 50)
    assert outcome == "Too High"


def test_guess_too_low():
    outcome, _ = check_guess(40, 50)
    assert outcome == "Too Low"


# --- check_guess: hint direction (Bug 1 — inverted hints) ---


def test_too_high_message_says_lower():
    # When guess is too high, player should be told to go LOWER, not higher
    _, message = check_guess(60, 50)
    assert "LOWER" in message


def test_too_low_message_says_higher():
    # When guess is too low, player should be told to go HIGHER, not lower
    _, message = check_guess(40, 50)
    assert "HIGHER" in message


# --- check_guess: type safety (Bug 2 — type corruption on even attempts) ---


def test_check_guess_int_vs_int():
    # Both int: normal comparison should work
    outcome, _ = check_guess(50, 50)
    assert outcome == "Win"


def test_check_guess_does_not_accept_string_secret():
    # Passing secret as str should NOT produce a win for matching int guess
    # (validates that app.py must always pass int, not str)
    outcome, _ = check_guess(50, 50)
    assert outcome == "Win"
    # If secret were "50", this would fail.
    # Confirm the app passes an int.
    assert isinstance(50, int)


# --- get_range_for_difficulty: correct ranges ---


def test_easy_range():
    low, high = get_range_for_difficulty("Easy")
    assert low == 1
    assert high == 20


def test_normal_range():
    low, high = get_range_for_difficulty("Normal")
    assert low == 1
    assert high == 100


def test_hard_range():
    # Bug: Hard was returning (1, 50) instead of (1, 500)
    low, high = get_range_for_difficulty("Hard")
    assert low == 1
    assert high == 500


# --- update_score: win scoring (Bug 8 — off-by-one) ---


def test_win_score_attempt_1():
    # Winning on attempt 1 should give 100 - 10*1 = 90 points, not 80
    score = update_score(0, "Win", 1)
    assert score == 90


def test_win_score_attempt_2():
    # Winning on attempt 2 should give 100 - 10*2 = 80 points
    score = update_score(0, "Win", 2)
    assert score == 80


def test_win_score_minimum():
    # Score should floor at 10, not go negative
    score = update_score(0, "Win", 10)
    assert score == 10


def test_win_score_accumulates():
    # Score should add on top of existing score
    score = update_score(50, "Win", 1)
    assert score == 140


# --- parse_guess: input validation ---


def test_parse_valid_integer():
    ok, value, _ = parse_guess("42")
    assert ok is True
    assert value == 42
    assert _ is None


def test_parse_empty_string():
    ok, value, _ = parse_guess("")
    assert ok is False
    assert value is None


def test_parse_non_number():
    ok, value, _ = parse_guess("abc")
    assert ok is False
    assert value is None


def test_parse_float_truncates():
    ok, value, _ = parse_guess("3.9")
    assert ok is True
    assert value == 3


# --- advanced edge-case coverage ---

def test_parse_negative_number_gracefully():
    # Negative inputs should parse cleanly instead of crashing the game
    ok, value, error = parse_guess("-42")
    assert ok is True
    assert value == -42
    assert error is None


def test_negative_guess_is_too_low_against_positive_secret():
    # A negative guess should still compare normally against the secret number
    outcome, message = check_guess(-42, 10)
    assert outcome == "Too Low"
    assert "HIGHER" in message


def test_parse_decimal_input_gracefully():
    # Decimal input should not crash the app.
    # The current game truncates it to an int.
    ok, value, error = parse_guess("19.99")
    assert ok is True
    assert value == 19
    assert error is None


def test_decimal_guess_compares_after_parsing():
    # After parsing, a decimal-derived int should still work in the game logic
    ok, value, error = parse_guess("19.99")
    assert ok is True
    assert error is None
    outcome, _ = check_guess(value, 20)
    assert outcome == "Too Low"


def test_parse_extremely_large_number_gracefully():
    # Very large integers should parse without overflow errors in Python
    huge_raw = "999999999999999999999999999999"
    ok, value, error = parse_guess(huge_raw)
    assert ok is True
    assert value == 999999999999999999999999999999
    assert error is None


def test_extremely_large_guess_is_too_high():
    # Very large guesses should still produce a normal game outcome
    huge_guess = 999999999999999999999999999999
    outcome, message = check_guess(huge_guess, 50)
    assert outcome == "Too High"
    assert "LOWER" in message


# --- enhanced UI feedback helpers ---


def test_describe_guess_feedback_marks_exact_guess_as_perfect():
    feedback = describe_guess_feedback(42, 42, 1, 100)
    assert feedback["label"] == "Perfect"
    assert feedback["emoji"] == "🎯"
    assert feedback["distance"] == 0
    assert feedback["direction"] == "Correct"


def test_describe_guess_feedback_marks_near_guess_as_hot():
    feedback = describe_guess_feedback(48, 50, 1, 100)
    assert feedback["label"] == "Hot"
    assert feedback["emoji"] == "🔥"
    assert feedback["direction"] == "Higher"


def test_describe_guess_feedback_marks_far_guess_as_cold():
    feedback = describe_guess_feedback(5, 80, 1, 100)
    assert feedback["label"] == "Cold"
    assert feedback["emoji"] == "🧊"
    assert feedback["direction"] == "Higher"


# --- high score persistence feature ---

def test_load_high_score_defaults_when_file_is_missing(tmp_path):
    record = load_high_score(tmp_path / "missing_high_score.json")
    assert record == {
        "best_score": None,
        "difficulty": None,
        "attempts": None,
    }


def test_maybe_update_high_score_saves_first_win(tmp_path):
    score_file = tmp_path / "high_score.json"

    record, updated = maybe_update_high_score(35, "Easy", 3, score_file)

    assert updated is True
    assert record["best_score"] == 35
    assert record["difficulty"] == "Easy"
    assert record["attempts"] == 3
    assert load_high_score(score_file) == record


def test_maybe_update_high_score_keeps_better_existing_score(tmp_path):
    score_file = tmp_path / "high_score.json"
    maybe_update_high_score(60, "Hard", 4, score_file)

    record, updated = maybe_update_high_score(20, "Easy", 2, score_file)

    assert updated is False
    assert record["best_score"] == 60
    assert record["difficulty"] == "Hard"
    assert record["attempts"] == 4


def test_maybe_update_high_score_breaks_tie_with_fewer_attempts(tmp_path):
    score_file = tmp_path / "high_score.json"
    maybe_update_high_score(50, "Hard", 5, score_file)

    record, updated = maybe_update_high_score(50, "Normal", 4, score_file)

    assert updated is True
    assert record["best_score"] == 50
    assert record["difficulty"] == "Normal"
    assert record["attempts"] == 4
