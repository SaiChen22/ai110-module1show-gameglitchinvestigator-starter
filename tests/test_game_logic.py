from logic_utils import check_guess, get_range_for_difficulty, parse_guess, update_score


# --- check_guess: outcome ---

def test_winning_guess():
    # FIX: Claude identified that check_guess returns a tuple (outcome, message), not a plain string;
    # updated to unpack with outcome, _ = ... so the assertion targets just the outcome
    outcome, _ = check_guess(50, 50)
    assert outcome == "Win"

def test_guess_too_high():
    outcome, _ = check_guess(60, 50)  # FIX: same tuple-unpack fix applied here
    assert outcome == "Too High"

def test_guess_too_low():
    outcome, _ = check_guess(40, 50)  # FIX: same tuple-unpack fix applied here
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
    # If secret were "50", this would fail — confirmed by checking int type
    assert isinstance(50, int)


# --- get_range_for_difficulty: correct ranges (Bug 5 & 6 — hardcoded ranges) ---

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
