"""Day 1 examples: plain asserts, fixtures, parametrize, markers, pytest.raises."""

import pytest

from digital_key import KeyError_, UnlockResult


# ---------------------------------------------------------------------------
# 1. Plain asserts + fixtures
# ---------------------------------------------------------------------------
@pytest.mark.smoke
def test_valid_key_can_unlock(key_manager, phone_key):
    result = key_manager.authorize(phone_key.key_id, phone_key.vehicle_id)
    assert result == UnlockResult.GRANTED


@pytest.mark.smoke
def test_register_stores_key(key_manager, phone_key):
    assert phone_key.key_id in key_manager.keys
    assert phone_key.owner == "Jasmin"
    assert not phone_key.revoked


# ---------------------------------------------------------------------------
# 2. Negative tests
# ---------------------------------------------------------------------------
@pytest.mark.negative
def test_unknown_key_is_rejected(key_manager, vehicle_ids):
    assert key_manager.authorize("NO-SUCH-KEY", vehicle_ids[0]) == UnlockResult.UNKNOWN_KEY


@pytest.mark.negative
def test_revoked_key_is_rejected(key_manager, revoked_key):
    result = key_manager.authorize(revoked_key.key_id, revoked_key.vehicle_id)
    assert result == UnlockResult.REVOKED


@pytest.mark.negative
def test_expired_key_is_rejected(key_manager, phone_key, future_time):
    result = key_manager.authorize(phone_key.key_id, phone_key.vehicle_id, now=future_time)
    assert result == UnlockResult.EXPIRED


@pytest.mark.negative
def test_key_cannot_unlock_other_vehicle(key_manager, phone_key, vehicle_ids):
    result = key_manager.authorize(phone_key.key_id, vehicle_ids[1])
    assert result == UnlockResult.WRONG_VEHICLE


# ---------------------------------------------------------------------------
# 3. pytest.raises: checking that errors are raised
# ---------------------------------------------------------------------------
@pytest.mark.negative
def test_duplicate_registration_raises(key_manager, phone_key):
    with pytest.raises(KeyError_, match="already registered"):
        key_manager.register(phone_key.key_id, phone_key.vehicle_id, owner="Someone")


# ---------------------------------------------------------------------------
# 4. Parametrize: one test function, many cases
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("command", ["unlock", "lock", "open_trunk"])
def test_all_valid_commands_are_granted(key_manager, phone_key, command):
    result = key_manager.authorize(phone_key.key_id, phone_key.vehicle_id, command=command)
    assert result == UnlockResult.GRANTED


@pytest.mark.negative
@pytest.mark.parametrize(
    "key_id, vehicle_id, valid_days",
    [
        ("", "R1S-001", 30),        # empty key id
        ("KEY-1", "", 30),          # empty vehicle id
        ("KEY-1", "R1S-001", 0),    # zero validity
        ("KEY-1", "R1S-001", -5),   # negative validity
    ],
    ids=["empty-key", "empty-vehicle", "zero-days", "negative-days"],
)
def test_invalid_registration_raises(key_manager, key_id, vehicle_id, valid_days):
    with pytest.raises(KeyError_):
        key_manager.register(key_id, vehicle_id, owner="Jasmin", valid_days=valid_days)


# ---------------------------------------------------------------------------
# 5. YOUR EXERCISES: remove the skip marker and write the test body
# ---------------------------------------------------------------------------
@pytest.mark.skip(reason="Exercise 1: write this test")
def test_invalid_command_raises(key_manager, phone_key):
    # Hint: authorize() with command="self_destruct" should raise KeyError_
    ...


@pytest.mark.skip(reason="Exercise 2: write this test")
def test_revoking_unknown_key_raises(key_manager):
    # Hint: use pytest.raises with match="not found"
    ...


@pytest.mark.skip(reason="Exercise 3: write this test")
def test_keys_for_vehicle_returns_only_that_vehicles_keys(key_manager, vehicle_ids):
    # Hint: register 2 keys on vehicle_ids[0] and 1 key on vehicle_ids[1],
    # then check keys_for_vehicle(vehicle_ids[0]) returns exactly 2 keys.
    ...


# Exercise 4: create a new fixture in conftest.py called "family_keys"
# that registers 3 keys (one per family member) on the same vehicle.
# Then write a test that revokes one and checks the other two still work.
