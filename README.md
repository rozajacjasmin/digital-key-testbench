# Digital Key Test Bench — Day 1: Python + Pytest

A small, simplified "digital key" system (register keys, revoke them, authorize
unlock) with a Pytest suite. The following days add a REST API, protobuf,
Pub/Sub, Appium and CI on top of it.

## 1. Set up (Git Bash)

```bash
cd digital-key-testbench

# Create and activate a virtual environment
python -m venv .venv
source .venv/Scripts/activate      # Windows (Git Bash)
# source .venv/bin/activate        # macOS / Linux

pip install pytest
```

## 2. Put it in Git and on GitHub

```bash
git init
git add .
git commit -m "Day 1: digital key model and pytest suite"

# Create an empty repo on github.com called digital-key-testbench, then:
git remote add origin https://github.com/<your-username>/digital-key-testbench.git
git branch -M main
git push -u origin main
```

## 3. Run the tests: try each command and see what changes

| Command | What it does |
|---|---|
| `pytest` | Run everything |
| `pytest -v` | Verbose: one line per test, including parametrize IDs |
| `pytest -k expired` | Only tests whose name contains "expired" |
| `pytest -m smoke` | Only tests marked `@pytest.mark.smoke` |
| `pytest -m "not negative"` | Everything except negative tests |
| `pytest -x` | Stop at the first failure |
| `pytest -s` | Show `print` output (see the session fixture setup/teardown) |
| `pytest --setup-show` | Show exactly when each fixture is created and torn down |
| `pytest -rs` | Show the reason for skipped tests |

`--setup-show` is the best way to understand fixture scope. Notice that
`vehicle_ids` (session) is created once, while `key_manager` (function) is
created fresh for every test.

## 4. Key concepts in this project

- **conftest.py**: shared fixtures, found automatically by Pytest
- **Fixture scope**: `function` (default, fresh per test) vs `session` (once per run)
- **yield fixtures**: code after `yield` is teardown and always runs
- **Fixtures using fixtures**: `phone_key` depends on `key_manager` and `vehicle_ids`
- **parametrize**: one test, many inputs, with readable `ids`
- **markers**: tag tests (`smoke`, `negative`) and select them with `-m`
- **pytest.raises**: assert that an exception is raised, optionally with `match=`

## 5. Your exercises

Open `tests/test_key_manager.py` and scroll to section 5:

1. `test_invalid_command_raises`
2. `test_revoking_unknown_key_raises`
3. `test_keys_for_vehicle_returns_only_that_vehicles_keys`
4. Write a `family_keys` fixture in `conftest.py` and a test that uses it

Remove each `@pytest.mark.skip(...)` line, write the test, and run
`pytest -v`. When everything passes, commit and push:

```bash
git add .
git commit -m "Day 1 exercises"
git push
```

**Bonus:** break the code on purpose (for example, remove the `revoked` check in
`authorize`) and see which tests catch it. That's a quick taste of mutation testing.
