# Day 3: Pub/Sub (event-driven testing) + CI with GitHub Actions

Around 3–4 hours. Part A is the most important. Part B is short but very
practical: after it, every `git push` runs your tests automatically.

> **Note:** the code files for Part A (`src/digital_key/events.py` and
> `tests/test_events.py`) don't exist yet. They get created when you start Day 3.
> Part B you build yourself from scratch.

## 0. Before you start

Day 1 and Day 2 are done. Check that everything is still green and pushed:

```bash
source .venv/Scripts/activate
pytest -v          # 42 passed
git status         # nothing to commit
```

Keep `LESSONS_LEARNED.md` open. Add to it when something today surprises you.

---

## Part A: Pub/Sub and event-driven testing (about 2–2.5 h)

### A1. What and why (read, 15 min)

So far every test has been **request → response**: you ask, the server answers
right away. Many real systems (vehicles included) don't work like that.
They send **events** through a **message broker**:

```
 phone app ──publish──►  topic "key-events"  ──deliver──►  vehicle
 (publisher)             (the broker)                     (subscriber)
```

- The publisher doesn't know who is listening, or whether anyone is.
- The subscriber gets the message **later**, not immediately.
- Real brokers: Google Pub/Sub, Kafka, MQTT, AWS SNS/SQS.

Example: you revoke a key in the app. The cloud publishes a `key_revoked` event.
The car receives it and stops accepting that key, maybe seconds later, maybe
after the car wakes up from sleep.

### A2. The three things that make it hard to test

| Problem | What happens | What the code must do |
|---|---|---|
| **Duplicates** | Brokers deliver *at least once*, so the same message can arrive twice | Be **idempotent**: handling it twice = handling it once |
| **Out of order** | `key_revoked` can arrive before `key_registered` | Not crash, and end up in the right state |
| **Delay** | The effect isn't there when your test checks | Wait *correctly* (not `time.sleep(5)` everywhere) |

These three are what testers at event-driven companies check every day.
Remember them. They're also good interview answers.

### A3. Today's code

- `src/digital_key/events.py`: a small **in-memory broker** (no network, no
  cloud account) and a `VehicleEventHandler` that listens to key events and
  updates the car's own list of allowed keys.
- `tests/test_events.py`: example tests plus exercises, same layout as before.

```bash
pytest -v tests/test_events.py
```

Read the tests from top to bottom. Notice:
- how a test **publishes** an event and then checks the **subscriber's** state
- how each event has a `message_id`, which is what makes duplicate detection possible
- the `wait_until(...)` helper: it checks a condition again and again until it's
  true or a timeout passes. That's the correct way to handle delay.

### A4. Exercises (1 h)

At the bottom of `tests/test_events.py`:

1. The same `key_registered` event delivered **twice** → the key is stored only once
2. `key_revoked` for a key the car has never seen → no crash
3. An event with an unknown type → ignored, and the handler keeps working
4. Revoke arriving **before** register → what *should* happen? Decide first,
   then write the test. (There's no single right answer. Write down your reasoning.)

### A5. Think about it (no code)

Why is `time.sleep(5)` in a test a bad idea? Give **two** reasons.
(Hint: think about a slow CI server, and about 500 tests.)

---

## Part B: CI with GitHub Actions (about 1 h)

### B1. What and why (read, 5 min)

**CI (Continuous Integration)** means: every time someone pushes code, a server
runs all the tests automatically. If something is red, everyone sees it before
it's merged. At work this is usually where you'll first see your tests fail,
not on your own machine.

### B2. Write down the dependencies

A CI server starts with an **empty** machine. It needs to know what to install.
Create `requirements-dev.txt` in the project root:

```
pytest
fastapi
uvicorn
httpx
protobuf
grpcio-tools
```

Check that it's complete: create a fresh venv, install **only** from this file,
and run `pytest`. If something is missing, you'll find out now instead of in CI.

### B3. Create the workflow

Create the file `.github/workflows/tests.yml`:

```yaml
name: tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements-dev.txt
      - run: python -m grpc_tools.protoc -I proto --python_out=src/digital_key proto/unlock.proto
      - run: pytest -v
```

Read it line by line. Can you say what each step does?
Why is the `protoc` step needed? (Hint: look at your `.gitignore`.)

**Line endings:** the CI server runs Linux (LF line endings) and you're on
Windows (CRLF), which is what the `LF will be replaced by CRLF` warnings were
about. To make the repo consistent for everyone, add a `.gitattributes` file in
the project root with this line:

```
* text=auto eol=lf
```

### B4. Push and watch it run

```bash
git add .
git commit -m "Day 3: CI with GitHub Actions"
git push
```

Open your repo on github.com → **Actions** tab. Click the run and open the log.

### B5. Exercises

1. **Break it on purpose.** Change one assert so it fails, push, and look at how
   the failure shows up in GitHub. Then fix it and push again.
2. **Two Python versions.** Use a `matrix` so the tests run on both 3.12 and 3.13.
   (Search for "GitHub Actions python matrix".)
3. **Smoke first.** Add a step that runs `pytest -m smoke` *before* the full run.
   Why could that be useful on a big project?
4. **Badge.** Add a status badge to `README.md` that shows green/red.

---

## When you're done

```bash
pytest -v                 # everything green locally
git add .
git commit -m "Day 3: Pub/Sub tests and CI"
git push                  # ... and green in the Actions tab
```

## Coming next: Appium (mobile app testing)

Reading only, 10 min. Appium drives a real mobile app (on an emulator or phone):
it taps buttons, types text and reads what's on screen, like a robot user.
The hard parts are **finding elements** reliably (IDs vs. text vs. XPath) and
**waiting** for the screen to update, which is the same "delay" problem you met
today with Pub/Sub. Setup needs Android Studio and an emulator, so plan some
extra time for it.
