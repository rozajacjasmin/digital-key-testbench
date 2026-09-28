"""Shared fixtures. Pytest finds this file automatically, so every
test file in this folder can use these fixtures without importing them."""

from datetime import datetime, timedelta, timezone

import pytest

from digital_key import DigitalKey, KeyManager


# --- Session scope: created ONCE for the whole test run -------------------
@pytest.fixture(scope="session")
def vehicle_ids():
    print("\n[setup] session: loading vehicle IDs")
    yield ["R1S-001", "R1T-002", "R2-003"]
    print("\n[teardown] session: done with vehicle IDs")


# --- Function scope (default): a fresh object for EVERY test -------------
@pytest.fixture
def key_manager():
    """An empty KeyManager. Each test gets its own, so tests never affect each other."""
    manager = KeyManager()
    yield manager
    # Everything after 'yield' is teardown. Runs even if the test fails.
    manager.keys.clear()


# --- Fixtures can use other fixtures ---------------------------------------
@pytest.fixture
def phone_key(key_manager, vehicle_ids):
    """A valid phone key registered to the first vehicle."""
    return key_manager.register("PHONE-JASMIN", vehicle_ids[0], owner="Jasmin")


@pytest.fixture
def revoked_key(key_manager, vehicle_ids):
    key = key_manager.register("PHONE-OLD", vehicle_ids[0], owner="Jasmin")
    key_manager.revoke(key.key_id)
    return key


@pytest.fixture
def future_time():
    """A point in time two years from now, used to test expiry."""
    return datetime.now(timezone.utc) + timedelta(days=730)

@pytest.fixture
def nbr_of_members():
    return 3

# Exercise 4: create a new fixture in conftest.py called "family_keys"
# that registers 3 keys (one per family member) on the same vehicle.
# Then write a test that revokes one and checks the other two still work.
@pytest.fixture
def family_keys(key_manager, vehicle_ids, nbr_of_members) -> list[DigitalKey]:
    return [
        key_manager.register(f"KEY-{i}", vehicle_ids[0], owner=f"Member {i}")
        for i in range(1, nbr_of_members + 1)
    ]
