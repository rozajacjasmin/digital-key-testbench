# Day 2: REST API testing + Protocol Buffers

Around 3–4 hours. Part A is the most important. Do Part B if you have time.

## 0. Install the new packages (Git Bash, venv active)

```bash
source .venv/Scripts/activate
pip install fastapi uvicorn httpx protobuf grpcio-tools
```

---

## Part A: REST API testing (about 2–2.5 h)

New files: `src/digital_key/api.py` (the server) and `tests/test_api.py` (the tests).

### A1. Start the server and click around (20 min)

```bash
uvicorn digital_key.api:app --reload --app-dir src
```

Open **http://127.0.0.1:8000/docs** in your browser. This is Swagger UI, an
interactive page generated from the code.

1. Try `GET /health` → **Try it out** → **Execute**
2. Try `POST /keys` **without** a token and look at the 401 answer
3. Each protected endpoint shows an **x-api-token** field. Type `test-token` there
4. Register a key, unlock with it, revoke it, try to unlock again

Stop the server with `Ctrl+C`.

### A2. Understand the key REST concepts

| Concept | In this project |
|---|---|
| **Method** | `GET` = read, `POST` = create/do, `DELETE` = remove |
| **Path** | `/vehicles/R1S-001/keys` (the `R1S-001` part is a *path parameter*) |
| **Header** | `X-API-Token` for authentication |
| **Body (JSON)** | `{"key_id": "K1", "command": "unlock"}` |
| **Status code** | the server's short answer (see below) |

Status codes used here, which you'll see every day at work:

| Code | Meaning | When |
|---|---|---|
| 200 | OK | request worked |
| 201 | Created | key registered |
| 204 | No Content | key revoked (nothing to return) |
| 400 | Bad Request | invalid command |
| 401 | Unauthorized | missing / wrong token |
| 403 | Forbidden | valid request, but not allowed (revoked, expired, wrong vehicle) |
| 404 | Not Found | key does not exist |
| 409 | Conflict | key already registered |
| 422 | Unprocessable | JSON is missing fields or has wrong types |

A good API test almost always checks **both** the status code and the body.

### A3. Run and read the tests (30 min)

```bash
pytest -v tests/test_api.py
```

Read `tests/test_api.py` from top to bottom. Notice:
- the `client` fixture creates a **fresh app per test**, so there is no shared state
- the `registered_key` fixture uses the API itself to set up data
- section 2 tests auth with `parametrize`
- section 4 tests a full user journey

### A4. Exercises (1 h)

At the bottom of `tests/test_api.py`: exercises 1–5.

### A5. Bonus: test a *running* server with `requests`

At work, many tests call a real server over the network. Start the server in one
Git Bash window, then in another:

```bash
pip install requests
python
```
```python
>>> import requests
>>> r = requests.get("http://127.0.0.1:8000/health")
>>> r.status_code, r.json()
```

`requests` and `TestClient` have almost the same interface (`.get`, `.post`,
`.status_code`, `.json()`), so everything you learn here carries over.

---

## Part B: Protocol Buffers (about 1 h)

### B1. What and why (read, 10 min)

JSON is text and easy to read, but big. Protobuf is **binary, small and fast**,
and both sides share a strict schema (`.proto` file). Vehicles and IoT devices
use it because bandwidth and battery matter.

### B2. Generate the Python code

Open `proto/unlock.proto` and read the comments. Then run:

```bash
python -m grpc_tools.protoc -I proto --python_out=src/digital_key proto/unlock.proto
```

This creates `src/digital_key/unlock_pb2.py`. Never edit it by hand. Change the
`.proto` file and regenerate instead.

### B3. Run the tests

```bash
pytest -v -s tests/test_proto.py
```

`-s` shows how many bytes protobuf saves compared with JSON.

### B4. Exercise

At the bottom of `tests/test_proto.py`.

---

## When you're done

```bash
pytest -v                 # everything should pass (except skipped exercises)
git add .
git commit -m "Day 2: REST API and protobuf tests"
git push
```

## Quick concept check for Pub/Sub and GraphQL (reading only, 15 min)

- **Pub/Sub**: senders *publish* messages to a **topic**; receivers *subscribe*.
  They never talk directly. Messages can arrive **more than once** or **out of
  order**, so tests should check duplicate handling and ordering.
- **GraphQL**: one endpoint (usually `POST /graphql`); the client says exactly
  which fields it wants. Errors often come back with status **200** and an
  `"errors"` list in the body, so **checking only the status code is not enough.**
