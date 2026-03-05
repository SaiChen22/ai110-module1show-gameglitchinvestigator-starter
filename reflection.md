# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

- What did the game look like the first time you ran it?
- List at least two concrete bugs you noticed at the start
  (for example: "the secret number kept changing" or "the hints were backwards").

When I first ran the game, it looked normal on the surface but was completely unwinnable. Even when I typed the exact secret number shown in the Developer Debug Info, I could not win. I found 8 bugs in total:

1. The hints were inverted — when my guess was too high, the game told me to "Go HIGHER", making it impossible to converge on the answer.
2. On every even-numbered attempt, the secret number was silently converted from an integer to a string, so the comparison `guess == secret` would always fail (e.g., `50 == "50"` is `False` in Python).
3. The "New Game" button always generated a secret in the range 1–100 regardless of difficulty, so Hard mode (1–500) was broken.
4. The range hint at the top said "Guess a number between 1 and 100" even on Easy (1–20) or Hard (1–500).
5. The attempts counter was initialized to 1 on first load but reset to 0 on "New Game", making the first game's attempt count off by one.
6. The win score calculation used `attempt_number + 1` instead of `attempt_number`, deducting 10 extra points from every win.
7. All three pytest tests always failed because `check_guess` returns a `(outcome, message)` tuple but the tests compared the full tuple to a plain string like `"Win"`.
8. The `except TypeError` fallback in `check_guess` used lexicographic string comparison (`"9" > "50"` evaluates to `True`), giving wrong hints when types were mixed.


---

## 2. How did you use AI as a teammate?

- Which AI tools did you use on this project (for example: ChatGPT, Gemini, Copilot)?
- Give one example of an AI suggestion that was correct (including what the AI suggested and how you verified the result).
- Give one example of an AI suggestion that was incorrect or misleading (including what the AI suggested and how you verified the result).

I used Claude Code as my primary AI assistant throughout this project. After each fix, I added `# FIX:` comments directly in the code explaining what was wrong, what was changed, and how Claude helped — for example, `# FIX: Removed even-attempt type corruption; Claude explained that int("50") != "50" in Python`.

One example of a correct suggestion: Claude identified the type corruption bug on even attempts (`secret = str(st.session_state.secret)`) and explained that `50 == "50"` evaluates to `False` in Python. I verified this by checking the Developer Debug Info while submitting on attempt 2 — the secret looked right visually but the comparison always failed.

One area where I had to verify carefully: Claude suggested adding a `conftest.py` to fix the `ModuleNotFoundError` when running `pytest`. At first I was unsure if this was the right approach versus adding a `pytest.ini`. I confirmed it worked by running `pytest tests/ -v` and seeing all 3 tests pass.

---

## 3. Debugging and testing your fixes

- How did you decide whether a bug was really fixed?
- Describe at least one test you ran (manual or using pytest)
  and what it showed you about your code.
- Did AI help you design or understand any tests? How?

I decided a bug was fixed only when I could verify the behavior directly — either by running `pytest` and seeing it pass, or by manually playing the game and confirming the correct outcome.

The most revealing test was running `pytest tests/ -v` after fixing the tuple mismatch. Before the fix, all three tests failed silently because `("Win", "🎉 Correct!") == "Win"` is always `False` in Python — no exception is thrown, the assertion just fails. After unpacking the tuple with `outcome, _ = check_guess(...)`, all three tests immediately passed, which also confirmed the hint inversion fix was correct at the same time.

Claude helped me understand why the tests were failing by pointing out that `check_guess` returns a tuple while the assertions expected a plain string. This also showed me the value of reading function signatures carefully before writing assertions.

---

## 4. What did you learn about Streamlit and state?

- In your own words, explain why the secret number kept changing in the original app.
- How would you explain Streamlit "reruns" and session state to a friend who has never used Streamlit?
- What change did you make that finally gave the game a stable secret number?

In the original app, the secret number did not actually change on its own — it was the type that changed. Every even attempt coerced `secret` into a string via `str(st.session_state.secret)`. So the stored number stayed the same, but the value passed to `check_guess` alternated between `int` and `str`, making comparisons fail on even attempts and appear to "change" behavior.

Streamlit reruns the entire Python script from top to bottom every time the user interacts with anything — clicking a button, typing in a field, or changing a sidebar setting all trigger a full rerun. Without `st.session_state`, every rerun would re-execute `secret = random.randint(...)` and generate a new number. `st.session_state` is like a notebook that persists between reruns: you write a value in once and it stays there until you explicitly change or clear it.

The fix that gave the game a stable secret was the guard already in place: `if "secret" not in st.session_state: st.session_state.secret = random.randint(low, high)`. This ensures the secret is only generated once per session. The real problem was the type corruption on even attempts, which I fixed by always passing `st.session_state.secret` directly to `check_guess` without any conditional casting.

---

## 5. Looking ahead: your developer habits

- What is one habit or strategy from this project that you want to reuse in future labs or projects?
  - This could be a testing habit, a prompting strategy, or a way you used Git.
- What is one thing you would do differently next time you work with AI on a coding task?
- In one or two sentences, describe how this project changed the way you think about AI generated code.

One habit I want to keep: reading the actual return type of a function before writing tests or calling it. The test/API mismatch bug (`check_guess` returning a tuple vs. tests expecting a string) would have been caught immediately if I had read the function signature first. In the future I'll always cross-check what a function returns against how it's consumed.

Next time I work with AI on a coding task, I would ask it to explain *why* a bug exists, not just what to change. Understanding the root cause (e.g., Python's `==` operator comparing type as well as value) stuck with me more than just seeing the fix.

This project changed how I think about AI-generated code: I used to assume that if the code runs without errors, it probably works. Now I know that subtle logic bugs — like inverted conditions or silent type coercions — can make code run fine while producing completely wrong results, and only careful reading or tests will catch them.

---

