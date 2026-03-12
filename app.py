import random
from pathlib import Path

import streamlit as st
from logic_utils import (
    check_guess,
    describe_guess_feedback,
    get_range_for_difficulty,
    load_high_score,
    maybe_update_high_score,
    parse_guess,
    update_score,
)


HIGH_SCORE_FILE = Path(__file__).with_name("high_score.json")


def render_feedback_panel(feedback, hint_message):
    """Render a color-coded hot/cold hint panel."""
    closeness_map = {
        "Perfect": "Exact",
        "Hot": "Very close",
        "Warm": "Close",
        "Cold": "Far",
    }
    closeness_text = closeness_map.get(feedback["label"], "Unknown")
    direction_text = (
        "You solved it."
        if feedback["direction"] == "Correct"
        else f"Try a {feedback['direction']} number next."
    )

    st.markdown(
        f"""
        <div style="
            background: {feedback['color']}26;
            border-left: 6px solid {feedback['color']};
            border-radius: 14px;
            padding: 1rem 1.25rem;
            margin: 0.75rem 0 1rem 0;
        ">
            <h4 style="margin: 0 0 0.35rem 0;">
                {feedback['emoji']} {feedback['label']} signal
            </h4>
            <p style="margin: 0 0 0.35rem 0;">
                <strong>{hint_message}</strong>
            </p>
            <p style="margin: 0;">
                Closeness: {closeness_text}. {direction_text}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_table_cell(value):
    """Escape values before placing them in a markdown table."""
    return str(value).replace("|", "\\|")


def render_session_table(rows):
    """Render a markdown table summarizing the game session."""
    if not rows:
        st.caption(
            "No guesses recorded yet. Submit a guess to populate the log."
        )
        return

    lines = [
        "| Attempt | Guess | Direction | Heat | Closeness | Score |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    format_table_cell(row["attempt"]),
                    format_table_cell(row["guess"]),
                    format_table_cell(row["direction"]),
                    format_table_cell(row["heat"]),
                    format_table_cell(row["distance"]),
                    format_table_cell(row["score"]),
                ]
            )
            + " |"
        )

    st.markdown("\n".join(lines))


st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮")

st.title("🎮 Game Glitch Investigator")
st.caption("An AI-generated guessing game. Something is off.")

st.sidebar.header("Settings")

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Normal", "Hard"],
    index=1,
)

attempt_limit_map = {
    "Easy": 6,
    "Normal": 8,
    "Hard": 5,
}
attempt_limit = attempt_limit_map[difficulty]

low, high = get_range_for_difficulty(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")

if "secret" not in st.session_state:
    st.session_state.secret = random.randint(low, high)

# FIX: Initialize attempts to 0 so it matches the new game reset state.
if "attempts" not in st.session_state:
    st.session_state.attempts = 0

if "score" not in st.session_state:
    st.session_state.score = 0

if "status" not in st.session_state:
    st.session_state.status = "playing"

if "history" not in st.session_state:
    st.session_state.history = []

if "high_score" not in st.session_state:
    st.session_state.high_score = load_high_score(str(HIGH_SCORE_FILE))

if "feedback_log" not in st.session_state:
    st.session_state.feedback_log = []

if "last_feedback" not in st.session_state:
    st.session_state.last_feedback = None

if "last_hint_message" not in st.session_state:
    st.session_state.last_hint_message = None

if "status_message" not in st.session_state:
    st.session_state.status_message = ""

st.sidebar.divider()
st.sidebar.subheader("🏆 High Score")
high_score = st.session_state.high_score

if high_score["best_score"] is None:
    st.sidebar.caption(
        "No saved wins yet. Win a round to create the first record."
    )
else:
    st.sidebar.metric("Best score", high_score["best_score"])
    st.sidebar.caption(f"Difficulty: {high_score['difficulty']}")
    st.sidebar.caption(f"Attempts used: {high_score['attempts']}")
    st.sidebar.caption(f"Saved to: {HIGH_SCORE_FILE.name}")

st.sidebar.subheader("🌡️ Heat Guide")
st.sidebar.caption("🔥 Hot = very close")
st.sidebar.caption("🌤️ Warm = getting closer")
st.sidebar.caption("🧊 Cold = far away")

st.subheader("Make a guess")

# FIX: Use the selected difficulty range instead of a hardcoded prompt.
st.info(
    f"Guess a number between {low} and {high}. "
    f"Attempts left: {attempt_limit - st.session_state.attempts}"
)

stats_col1, stats_col2, stats_col3 = st.columns(3)
stats_col1.metric("Current score", st.session_state.score)
stats_col2.metric(
    "Attempts left",
    max(attempt_limit - st.session_state.attempts, 0),
)
stats_col3.metric(
    "Best score",
    high_score["best_score"] if high_score["best_score"] is not None else "—",
)

st.progress(
    min(st.session_state.attempts / attempt_limit, 1.0),
    text=(
        f"{st.session_state.attempts} of {attempt_limit} attempts used"
    ),
)

with st.expander("Developer Debug Info"):
    st.write("Secret:", st.session_state.secret)
    st.write("Attempts:", st.session_state.attempts)
    st.write("Score:", st.session_state.score)
    st.write("Difficulty:", difficulty)
    st.write("History:", st.session_state.history)
    st.write("Feedback Log:", st.session_state.feedback_log)

game_locked = st.session_state.status != "playing"

raw_guess = st.text_input(
    "Enter your guess:",
    key=f"guess_input_{difficulty}",
    disabled=game_locked,
)

col1, col2, col3 = st.columns(3)
with col1:
    submit = st.button("Submit Guess 🚀", disabled=game_locked)
with col2:
    new_game = st.button("New Game 🔁")
with col3:
    show_hint = st.checkbox("Show hint", value=True)

# FIX: Reset status, history, and score along with attempts and secret.
# Also keep the secret within the active difficulty range.
if new_game:
    st.session_state.attempts = 0
    st.session_state.secret = random.randint(low, high)
    st.session_state.status = "playing"
    st.session_state.status_message = ""
    st.session_state.history = []
    st.session_state.score = 0
    st.session_state.feedback_log = []
    st.session_state.last_feedback = None
    st.session_state.last_hint_message = None
    st.rerun()

if submit and st.session_state.status == "playing":
    st.session_state.attempts += 1

    ok, guess_int, err = parse_guess(raw_guess)

    if not ok:
        st.session_state.history.append(raw_guess)
        st.session_state.last_feedback = None
        st.session_state.last_hint_message = err
        st.session_state.feedback_log.append(
            {
                "attempt": st.session_state.attempts,
                "guess": raw_guess or "(empty)",
                "direction": "Invalid",
                "heat": "⚠️ Retry",
                "distance": "Unknown",
                "score": st.session_state.score,
            }
        )
    else:
        assert guess_int is not None
        st.session_state.history.append(guess_int)

        # FIX: Keep the secret as an int so wins still work on every attempt.
        outcome, message = check_guess(guess_int, st.session_state.secret)
        feedback = describe_guess_feedback(
            guess_int,
            st.session_state.secret,
            low,
            high,
        )
        st.session_state.last_feedback = feedback
        st.session_state.last_hint_message = message

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
        )
        st.session_state.feedback_log.append(
            {
                "attempt": st.session_state.attempts,
                "guess": guess_int,
                "direction": feedback["direction"],
                "heat": f"{feedback['emoji']} {feedback['label']}",
                "distance": {
                    "Perfect": "Exact",
                    "Hot": "Very close",
                    "Warm": "Close",
                    "Cold": "Far",
                }.get(feedback["label"], "Unknown"),
                "score": st.session_state.score,
            }
        )

        if outcome == "Win":
            (
                st.session_state.high_score,
                is_new_high_score,
            ) = maybe_update_high_score(
                current_score=st.session_state.score,
                difficulty=difficulty,
                attempt_number=st.session_state.attempts,
                score_file=str(HIGH_SCORE_FILE),
            )
            st.balloons()
            st.session_state.status = "won"
            st.session_state.status_message = (
                "You won! "
                f"Final score: {st.session_state.score}"
            )
            if is_new_high_score:
                st.session_state.status_message += (
                    " 🏆 New high score saved."
                )
        elif st.session_state.attempts >= attempt_limit:
            st.session_state.status = "lost"
            st.session_state.status_message = (
                "Out of attempts! Start a new game to try again. "
                f"Score: {st.session_state.score}"
            )

if show_hint and st.session_state.last_feedback is not None:
    render_feedback_panel(
        st.session_state.last_feedback,
        st.session_state.last_hint_message,
    )
elif show_hint and st.session_state.last_hint_message:
    st.error(st.session_state.last_hint_message)

if st.session_state.status == "won":
    st.success(st.session_state.status_message)
elif st.session_state.status == "lost":
    st.error(st.session_state.status_message)

st.subheader("📊 Session Summary")
st.caption(
    "Track each guess, how close it was, and how your score changed "
    "throughout the round."
)
render_session_table(st.session_state.feedback_log)

st.divider()
st.caption("Built by an AI that claims this code is production-ready.")
