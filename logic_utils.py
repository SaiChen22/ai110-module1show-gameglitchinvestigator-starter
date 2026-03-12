import json
from pathlib import Path
from typing import TypedDict


class HighScoreRecord(TypedDict):
    """Typed structure for persisted high score data."""

    best_score: int | None
    difficulty: str | None
    attempts: int | None


class GuessFeedback(TypedDict):
    """Typed structure for UI-ready guess feedback."""

    label: str
    emoji: str
    color: str
    distance: int
    direction: str


def get_default_high_score() -> HighScoreRecord:
    """Return the default high score payload used by the app."""
    return {
        "best_score": None,
        "difficulty": None,
        "attempts": None,
    }


def load_high_score(
    score_file: str | Path = "high_score.json",
) -> HighScoreRecord:
    """Load the persisted high score from disk, or return defaults."""
    path = Path(score_file)
    default_score = get_default_high_score()

    if not path.exists():
        return default_score

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default_score

    if not isinstance(data, dict):
        return default_score

    best_score = data.get("best_score")
    difficulty = data.get("difficulty")
    attempts = data.get("attempts")

    return {
        "best_score": best_score if isinstance(best_score, int) else None,
        "difficulty": difficulty if isinstance(difficulty, str) else None,
        "attempts": attempts if isinstance(attempts, int) else None,
    }


def save_high_score(
    record: HighScoreRecord,
    score_file: str | Path = "high_score.json",
) -> HighScoreRecord:
    """Persist a high score payload to disk and return it."""
    normalized_record: HighScoreRecord = {
        "best_score": record.get("best_score"),
        "difficulty": record.get("difficulty"),
        "attempts": record.get("attempts"),
    }
    path = Path(score_file)
    path.write_text(json.dumps(normalized_record, indent=2), encoding="utf-8")
    return normalized_record


def maybe_update_high_score(
    current_score: int,
    difficulty: str,
    attempt_number: int,
    score_file: str | Path = "high_score.json",
) -> tuple[HighScoreRecord, bool]:
    """Save a new high score when the latest win beats the stored record."""
    current_record = load_high_score(score_file)
    best_score = current_record["best_score"]
    best_attempts = current_record["attempts"]

    is_better_score = best_score is None or current_score > best_score
    is_tie_with_fewer_attempts = (
        best_score is not None
        and current_score == best_score
        and (best_attempts is None or attempt_number < best_attempts)
    )

    if is_better_score or is_tie_with_fewer_attempts:
        updated_record: HighScoreRecord = {
            "best_score": current_score,
            "difficulty": difficulty,
            "attempts": attempt_number,
        }
        save_high_score(updated_record, score_file)
        return updated_record, True

    return current_record, False


def get_range_for_difficulty(difficulty: str):
    """Return (low, high) inclusive range for a given difficulty."""
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 100
    if difficulty == "Hard":
        # FIX: Match the documented hard-mode range.
        return 1, 500
    return 1, 100


def parse_guess(raw: str):
    """
    Parse user input into an int guess.

    Returns: (ok: bool, guess_int: int | None, error_message: str | None)
    """
    if raw is None:
        return False, None, "Enter a guess."

    if raw == "":
        return False, None, "Enter a guess."

    try:
        if "." in raw:
            value = int(float(raw))
        else:
            value = int(raw)
    except Exception:
        return False, None, "That is not a number."

    return True, value, None


def check_guess(guess, secret):
    """
    Compare guess to secret and return (outcome, message).

    outcome examples: "Win", "Too High", "Too Low"
    """
    if guess == secret:
        return "Win", "🎉 Correct!"

    # FIX: Correct the higher/lower hint direction.
    if guess > secret:
        return "Too High", "📉 Go LOWER!"

    return "Too Low", "📈 Go HIGHER!"


def describe_guess_feedback(
    guess: int,
    secret: int,
    low: int,
    high: int,
) -> GuessFeedback:
    """Describe how close a guess is for the enhanced UI."""
    distance = abs(secret - guess)
    total_span = max(high - low, 1)

    if distance == 0:
        return {
            "label": "Perfect",
            "emoji": "🎯",
            "color": "#16a34a",
            "distance": 0,
            "direction": "Correct",
        }

    hot_threshold = max(2, total_span // 20)
    warm_threshold = max(5, total_span // 8)

    if distance <= hot_threshold:
        label = "Hot"
        emoji = "🔥"
        color = "#ef4444"
    elif distance <= warm_threshold:
        label = "Warm"
        emoji = "🌤️"
        color = "#f59e0b"
    else:
        label = "Cold"
        emoji = "🧊"
        color = "#3b82f6"

    direction = "Lower" if guess > secret else "Higher"

    return {
        "label": label,
        "emoji": emoji,
        "color": color,
        "distance": distance,
        "direction": direction,
    }


def update_score(current_score: int, outcome: str, attempt_number: int):
    """Update score based on outcome and attempt number."""

    if outcome == "Win":
        # FIX: Score wins directly from the actual attempt number.
        points = 100 - 10 * attempt_number
        if points < 10:
            points = 10
        return current_score + points

    if outcome == "Too High":
        if attempt_number % 2 == 0:
            return current_score + 5
        return current_score - 5

    if outcome == "Too Low":
        return current_score - 5

    return current_score
