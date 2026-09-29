"""Day 2: REST API tests.

TestClient sends real HTTP requests to the app without starting a server,
so the tests are fast and need no network.
"""

import pytest
from fastapi.testclient import TestClient

from digital_key.api import API_TOKEN, create_app

AUTH = {"X-API-Token": API_TOKEN}


# ---------------------------------------------------------------------------
# Fixtures (these could live in conftest.py, kept here so the file is self-contained)
# ---------------------------------------------------------------------------
@pytest.fixture
def client():
    """A test client for a brand-new app. Every test starts with no keys."""
    return TestClient(create_app())


@pytest.fixture
def registered_key(client):
    """Register one key through the API and return its JSON."""
    payload = {"key_id": "PHONE-JASMIN", "vehicle_id": "R1S-001", "owner": "Jasmin"}
    response = client.post("/keys", json=payload, headers=AUTH)
    assert response.status_code == 201
    return response.json()


# ---------------------------------------------------------------------------
# 1. The basics: status code + response body
# ---------------------------------------------------------------------------
@pytest.mark.smoke
def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.smoke
def test_register_key_returns_201_and_the_key(client):
    payload = {"key_id": "KEY-1", "vehicle_id": "R1S-001", "owner": "Jasmin"}

    response = client.post("/keys", json=payload, headers=AUTH)

    assert response.status_code == 201
    body = response.json()
    assert body["key_id"] == "KEY-1"
    assert body["vehicle_id"] == "R1S-001"
    assert body["revoked"] is False


@pytest.mark.smoke
def test_valid_key_can_unlock(client, registered_key):
    response = client.post(
        f"/vehicles/{registered_key['vehicle_id']}/commands",
        json={"key_id": registered_key["key_id"], "command": "unlock"},
        headers=AUTH,
    )

    assert response.status_code == 200
    assert response.json()["result"] == "granted"


# ---------------------------------------------------------------------------
# 2. Authentication: every protected endpoint must reject bad tokens
# ---------------------------------------------------------------------------
@pytest.mark.negative
@pytest.mark.parametrize(
    "headers",
    [{}, {"X-API-Token": "wrong"}, {"X-API-Token": ""}],
    ids=["missing", "wrong", "empty"],
)
def test_register_without_valid_token_is_rejected(client, headers):
    payload = {"key_id": "KEY-1", "vehicle_id": "R1S-001", "owner": "Jasmin"}

    response = client.post("/keys", json=payload, headers=headers)

    assert response.status_code == 401


# ---------------------------------------------------------------------------
# 3. Error handling: the right status code for each problem
# ---------------------------------------------------------------------------
@pytest.mark.negative
def test_duplicate_key_returns_409(client, registered_key):
    response = client.post("/keys", json=registered_key | {"owner": "Someone"}, headers=AUTH)

    assert response.status_code == 409
    assert "already registered" in response.json()["detail"]


@pytest.mark.negative
def test_missing_field_returns_422(client):
    # "owner" is missing. FastAPI validates the JSON and answers 422 automatically.
    response = client.post("/keys", json={"key_id": "KEY-1", "vehicle_id": "R1S-001"}, headers=AUTH)

    assert response.status_code == 422


@pytest.mark.negative
def test_revoked_key_cannot_unlock(client, registered_key):
    client.delete(f"/keys/{registered_key['key_id']}", headers=AUTH)

    response = client.post(
        f"/vehicles/{registered_key['vehicle_id']}/commands",
        json={"key_id": registered_key["key_id"]},
        headers=AUTH,
    )

    assert response.status_code == 403
    assert response.json()["result"] == "revoked"


# ---------------------------------------------------------------------------
# 4. A full flow, step by step, like a real user journey
# ---------------------------------------------------------------------------
def test_key_lifecycle_register_use_revoke(client):
    vehicle = "R1T-002"

    # Register
    r = client.post("/keys", json={"key_id": "K1", "vehicle_id": vehicle, "owner": "Jasmin"}, headers=AUTH)
    assert r.status_code == 201

    # It shows up in the vehicle's key list
    r = client.get(f"/vehicles/{vehicle}/keys", headers=AUTH)
    assert [k["key_id"] for k in r.json()] == ["K1"]

    # It can unlock
    r = client.post(f"/vehicles/{vehicle}/commands", json={"key_id": "K1"}, headers=AUTH)
    assert r.json()["result"] == "granted"

    # Revoke it
    r = client.delete("/keys/K1", headers=AUTH)
    assert r.status_code == 204

    # Now it is rejected, and the list shows it as revoked
    r = client.post(f"/vehicles/{vehicle}/commands", json={"key_id": "K1"}, headers=AUTH)
    assert r.status_code == 403
    r = client.get(f"/vehicles/{vehicle}/keys", headers=AUTH)
    assert r.json()[0]["revoked"] is True


# ---------------------------------------------------------------------------
# 5. YOUR EXERCISES: remove the skip line and write the test body
# ---------------------------------------------------------------------------
def test_revoking_unknown_key_returns_404(client):
    response = client.delete("/keys/NO-SUCH-KEY", headers=AUTH)

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_invalid_command_returns_400(client, registered_key):
    vehicle = registered_key["vehicle_id"]
    key_id = registered_key["key_id"]
    
    response = client.post(
        f"/vehicles/{vehicle}/commands",
        json={"key_id": key_id, "command": "self_destruct"},
        headers=AUTH
    )

    assert response.status_code == 400
    assert "invalid command" in response.json()["detail"]


def test_key_cannot_unlock_other_vehicle(client, registered_key):
    # Hint: send the command to "R2-003" instead. Expect 403 and result "wrong_vehicle".
    key_id = registered_key["key_id"]
    vehicle_id = "R2-003"

    assert registered_key["vehicle_id"] != vehicle_id, "precondition: key must belong to another car"

    response = client.post(
        f"/vehicles/{vehicle_id}/commands",
        json={"key_id": key_id, "command": "unlock"},
        headers=AUTH,
    )

    assert response.status_code == 403
    assert response.json()["result"] == "wrong_vehicle"


@pytest.mark.parametrize("command", ["unlock", "lock", "open_trunk"])
def test_all_valid_commands_are_granted(client, registered_key, command):
    vehicle = registered_key["vehicle_id"]
    key_id = registered_key["key_id"]
    
    response = client.post(
        f"/vehicles/{vehicle}/commands",
        json={"key_id": key_id, "command": command},
        headers=AUTH,
    )

    assert response.status_code == 200
    assert response.json()["result"] == "granted"


# Exercise 5: add a test that GET /vehicles/{id}/keys without a token returns 401.
# Question to think about: should /health need a token? Why or why not?
def test_list_keys_without_token_returns_401(client, registered_key):
    vehicle = registered_key["vehicle_id"]
    
    response = client.get(f"/vehicles/{vehicle}/keys")

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid or missing API token"
