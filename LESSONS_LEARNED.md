# Lessons learned

Things worth remembering for work, collected while doing the Day 1–3
exercises. Each section ends with a line you can say out loud to a colleague.

---

## 1. Writing good tests

### A green test can still be wrong
My "wrong vehicle" test used `"RS-003"` instead of `"R2-003"`, and it still
passed, because any car that isn't the key's own car gives `wrong_vehicle`.
The test passed, but not for the reason I intended.

- After a test goes green, read it once more and ask: *is it really testing what I think?*
- A good trick: break the code on purpose and check that the test turns red.

### Break exactly one rule per negative test
A request missing **both** `key_id` and `command` only passed because
`validate` happens to check `key_id` first. If someone reorders the checks, the
test breaks for no real reason.

```python
# Good: everything valid except the one thing under test
msg = pb.UnlockRequest(vehicle_id="R1S-001", command=pb.UNLOCK)  # no key_id
```

### `in` vs `==` in asserts
| Value | Use | Example |
|---|---|---|
| Free text (error messages) | `in` for the important phrase | `assert "not found" in body["detail"]` |
| Fixed values (status, enum, ids) | `==` for the exact value | `assert body["result"] == "wrong_vehicle"` |

`==` on a message is stricter but breaks when the wording changes. Choose on purpose.

### Actual on the left, expected on the right
```python
assert response.status_code == 403
assert response.json()["result"] == "wrong_vehicle"
```
Every assert reads the same way: *what I got == what I expected*.

### Arrange, Act, Assert
Split a test into three blocks with blank lines: **set up**, **do the thing**,
**check the result**. Anyone can see at a glance what the test does.

### Guard assertions make hidden assumptions visible
```python
assert registered_key["vehicle_id"] != vehicle_id, "precondition: key must belong to another car"
```
If the setup changes later, the failure points at the real cause instead of a
confusing `assert 200 == 403`.

### Always check *why* it failed, not just *that* it failed
Use `match=` with `pytest.raises` and check `detail` in API errors. Otherwise a
test can pass because the **wrong** rule raised the error.

### `print` is not a test
A `print` checks nothing, and nobody sees it unless you run `pytest -s`.
Use it to explore, then replace it with an `assert`.

### Test names should say what *should* happen
`test_all_valid_commands_are_granted` beats `test_all_valid_commands`.
When a test fails in CI, the name alone should tell you what broke.

> **Say it at work:** "A passing test only proves something if it would fail
> when the behavior is wrong."

---

## 2. pytest techniques

| Tool | What it does |
|---|---|
| `@pytest.fixture` | Reusable setup; pytest matches it to a test parameter **by name** |
| `yield` in a fixture | Code after `yield` is teardown and always runs |
| `scope="session"` | Created once per run instead of once per test |
| `@pytest.mark.parametrize` | One test function, many cases; each case is reported separately |
| `pytest.raises(Error, match="...")` | The test **passes only if** the error is raised |
| `pytest.importorskip(...)` | Skip the file if a module is missing, instead of crashing |
| `-v` / `-k name` / `-m smoke` / `-s` / `-x` | Verbose / filter by name / by marker / show prints / stop at first failure |

### Testing "this should NOT raise"
Just call the function. If it raises, pytest fails the test automatically.
```python
def test_valid_request():
    validate(make_request())  # passes if no error is raised
```
Don't write `assert validate(...)`. The function returns `None`, which is falsy,
so the assert always fails.

### Import order with `importorskip`
Imports that depend on an optional module must come **after** the
`importorskip` line, or the file crashes before it can skip. Mark it with
`# noqa: E402` and a reason, so linters know it's on purpose.

---

## 3. REST API testing

### Where to find what endpoints exist
| Source | What it is |
|---|---|
| **OpenAPI / Swagger** (`/docs`, `/openapi.json`) | Most common for REST |
| **Postman collection** | Ready-made requests, common in test teams |
| **`.proto` files** | The contract for protobuf / gRPC APIs |
| **Wiki / Confluence** | Often out of date |
| **Source code** | The final truth |

First-week question: *"Where's the API spec for the services I'll test, and is there a Postman collection?"*

### Documentation is often incomplete
`/docs` showed only **201** and **422** for `POST /keys`, but the code also
returns **401**, **409** and **400**. FastAPI can't see errors raised inside a
function. Tests pin down the **real** behavior.

### Status codes
| Code | Meaning |
|---|---|
| 200 / 201 / 204 | OK / Created / OK with no body |
| 400 | Bad request (e.g. invalid command) |
| 401 | Not authenticated (missing/wrong token) |
| 403 | Authenticated, but not allowed |
| 404 | Not found |
| 409 | Conflict (e.g. already exists) |
| 422 | Body has missing fields or wrong types |
| 500 | Server error, almost always a bug |

A good API test checks **both** the status code **and** the body.

### `DELETE` doesn't always delete (soft delete)
`DELETE /keys/{id}` only marked the key `revoked: true`. It stayed in the list.
Common in security systems, to keep history. When the method name and the
behavior don't match, **raise it with the team**: intended or bug?

### Authentication has two sides
1. Protected endpoints must reject requests without a token (**401**).
2. Public endpoints must **stay** public.

`/health` should **not** need a token: it's called by load balancers,
Kubernetes and monitoring, which don't have tokens, and it exposes nothing
sensitive. If it ever returned internal details, it should be protected.

Test every protected endpoint in one parametrized test. The list works as a
checklist of what must stay locked.

> **Say it at work:** "A test encodes a decision. Before writing it, find out
> what *should* happen, especially when nobody has written it down."

---

## 4. Protocol Buffers

- Binary, small and fast. Sender and receiver share a strict schema (`.proto`).
- The numbers in `string key_id = 2;` are **field IDs**, not values.
- Generated code (`unlock_pb2.py`) is never edited by hand. Change the `.proto` and regenerate.

### Why proto3 defaults are dangerous
proto3 **can't tell "not sent" from "sent as the default value"**. If the app
forgets a field, the receiver gets `""`, `0` or the first enum value, with no
error.

- **With JSON**, a missing field is visible, and FastAPI answered 422 automatically.
- **With proto3**, the bug turns silently into a valid-looking message.

Consequences:
- **Wrong actions:** if the first enum value were `UNLOCK`, a forgotten command
  would unlock the car. That's why `COMMAND_UNSPECIFIED = 0` comes first.
- **Wrong data:** `timestamp_ms = 0` means 1970, which can open the door to
  **replay attacks** if it's not checked.
- **Hidden bugs:** nothing crashes, nothing is logged, and the system quietly
  does the wrong thing.

What to do: validate every important field on the receiving side, and test the
"not set" case for each one.

> **Say it at work:** "proto3 can't distinguish 'not set' from 'set to the
> default', so every important field needs explicit validation, and tests for
> the unset case."

---

## 5. Writing the code under test

### One rule, one `if`, one clear message
My first `validate` used `if not request.command or not request.key_id:`.
Because `COMMAND_UNSPECIFIED` is `0`, and `0` is falsy, that line caught the
missing command too, with the message *"key_id and vehicle_id are required"*.
The second `if` could never run (dead code).

- A misleading error message is almost a bug in itself. Someone will debug the wrong thing.
- Compare with what you mean (`== pb.COMMAND_UNSPECIFIED`) instead of relying on "0 is falsy".

### Keep code and tests apart
Validation goes in `src/digital_key/validation.py`, tests in `tests/`.
Tests **use** the code; they don't contain it.

---

## 6. Python gotchas

| Mistake | What happens | Fix |
|---|---|---|
| `validate(make_request)` | Passes the function, not its result → `'function' object has no attribute ...` | `validate(make_request())` |
| `for n in keys: keys[n]` | `n` is already the item, not an index | `for key in keys: key.key_id` |
| `family_keys.` shows only list methods | It's a list; the attributes are on the items | `family_keys[0].` or loop |
| `response.json()[0]["..."]` on an error | The body is a dict, not a list | `response.json()["detail"]` |

---

## 7. Tools and editor

- **VS Code + src layout:** Pylance needs `"python.analysis.extraPaths": ["src"]`,
  because `pythonpath` in `pyproject.toml` only applies to pytest.
- **Autocomplete on fixtures:** Pylance may lose the item type of a list
  fixture. Fix it with `-> list[DigitalKey]` on the fixture. Type hints help
  both the editor and colleagues.
- **Hover over a variable** to see what type the editor thinks it is. That's the quickest way to debug "autocomplete doesn't work".
- **Reading existing tests** is one of the best ways to learn a new codebase:
  they show how the code is *meant* to be used.
- **Style that linters check:** two blank lines between top-level functions,
  trailing commas in multi-line calls, one quote style (`"`).

---

## 8. Event-driven systems (Pub/Sub)

Publishers send events to a **topic**; subscribers receive them **later**.
They never talk directly. Three things make this hard to test:

| Problem | What the code must do | How to test it |
|---|---|---|
| **Duplicates** (at-least-once delivery) | Be **idempotent**, e.g. skip a `message_id` it has already handled | Publish the **same event object** twice |
| **Out of order** | End up in the right state anyway | Publish the events in the "wrong" order |
| **Delay** | (nothing, it's just how brokers work) | Wait for a **condition**, not a fixed time |

### A duplicate means the same `message_id`
Two events with the same content but different ids are two different messages.
Two different messages (register and revoke) never share an id. Giving them the
same id made my out-of-order test pass for the wrong reason: the second one was
dropped as a duplicate.

### Check that something *happened*, not only that nothing crashed
My first duplicate test passed with `processed_ids == []`: the event went to the
wrong vehicle and nothing was handled at all. Assert on the **effect**
(`can_unlock(...)`) **and** on the bookkeeping (`len(processed_ids) == 1`).

### One bad message must not stop the rest
A "poison message" (unknown type, broken data) must be ignored, and the next
normal message must still work. Test both halves.

### Out of order is a design question first
*Revoke arrives before register: should the key work?* **No.** Revoke was the
owner's latest intention and a security action, so the system must **fail safe**
(deny) rather than **fail open**. The code let the key work, so the test found a
real bug. Real fixes: **tombstones** (remember revoked keys), **version/sequence
numbers**, or sender timestamps.

> **Say it at work:** "In event-driven systems I always test duplicates,
> out-of-order delivery and poison messages, and I decide the expected
> behavior before I write the test."

---

## 9. Waiting and flaky tests

`time.sleep(5)` in a test is wrong in both directions:
- **Too slow** when things are fast: it always waits 5 s (500 tests = 40+ min).
- **Too short** when things are slow: on a busy CI server it fails at random.

A test that sometimes passes and sometimes fails, without any code change, is
**flaky**. Flaky tests make people ignore red builds, and then real bugs slip through.

Use a polling helper instead: check the condition every few ms and return as
soon as it's true, with a generous timeout.

```python
wait_until(lambda: vehicle.can_unlock("PHONE-JASMIN"))
```

> **Say it at work:** "Wait for a condition, not for a fixed time."

---

## 10. Known bugs: `xfail`

When a test correctly finds a bug that won't be fixed right away, don't delete
it and don't change the assert. Mark it:

```python
@pytest.mark.xfail(reason="BUG-1234: revoke before register re-enables the key", strict=True)
```

- It still runs, and shows as `x` instead of red, so CI stays green.
- `strict=True` turns it **red** if it suddenly passes, so whoever fixes the bug
  remembers to remove the marker.
- While it's marked, it protects nothing. Changing an assert inside it had no
  visible effect, because the test was already failing.
- A test stops at the **first** failing assert. The ones after it never run.

---

## 11. CI with GitHub Actions

- **CI** runs every test on a clean machine on every push. It's usually where
  you'll first see your tests fail at work.
- **`requirements-dev.txt`** lists everything CI must install. Check it with a
  **fresh venv** (`python -m venv .venv-check`, `pip install -r ...`, `pytest`).
  Your own venv can hide missing packages ("works on my machine").
- **`which python`** shows which venv is active. Check it when something is odd.
- **Generated files** (`unlock_pb2.py`) go in `.gitignore` and are regenerated
  in CI with a build step.
- **Steps run top to bottom; a failing step stops the job.** Running
  `pytest -m smoke` first means **fail fast**: quick feedback, lower CI cost,
  shorter queues.
- **Matrix** runs the same job on several Python versions in parallel. Always
  **quote** versions in YAML: `["3.12", "3.13"]`. Unquoted, `3.10` becomes `3.1`.
- **Version pins** (`actions/checkout@v4`, `ubuntu-latest`) need looking after.
  Deprecation warnings in the Actions log are early warnings, not errors.
- **Line endings:** Windows uses CRLF, Linux uses LF. `.gitattributes` with
  `* text=auto eol=lf` keeps a mixed team consistent.
- **`.gitignore`** only affects files Git isn't tracking yet. For committed files,
  use `git rm --cached <file>`.
- **Don't add a package just to silence a warning.** A deprecation warning isn't
  an error. Change dependencies on purpose, in their own commit.

> **Say it at work:** "I check new dependencies in a fresh environment, and I
> put smoke tests first so the pipeline fails fast."
