"""Day 3: testing event-driven code (Pub/Sub).

The pattern in every test: PUBLISH an event, then CHECK the subscriber's state.
"""

import time
import uuid

import pytest

from digital_key.events import InMemoryBroker, KeyEvent, VehicleEventHandler

TOPIC = "key-events"
VEHICLE = "R1S-001"


# ---------------------------------------------------------------------------
# Helpers and fixtures
# ---------------------------------------------------------------------------
def make_event(event_type, key_id="PHONE-JASMIN", vehicle_id=VEHICLE, message_id=None):
    """Build an event. Each call gets a new unique message_id unless you pass one."""
    return KeyEvent(
        message_id=message_id or str(uuid.uuid4()),
        event_type=event_type,
        key_id=key_id,
        vehicle_id=vehicle_id,
    )


def wait_until(condition, timeout=2.0, interval=0.01):
    """Check condition() again and again until it's True, or fail after timeout.

    This is the right way to wait for something asynchronous: it returns as
    soon as the condition is met, and only waits the full timeout if it never is.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return
        time.sleep(interval)
    raise AssertionError(f"condition not met within {timeout}s")


@pytest.fixture
def broker():
    """A broker that delivers immediately. Good for testing the logic."""
    return InMemoryBroker()


@pytest.fixture
def vehicle(broker):
    """A vehicle subscribed to the key-events topic."""
    handler = VehicleEventHandler(VEHICLE)
    broker.subscribe(TOPIC, handler.handle)
    return handler


# ---------------------------------------------------------------------------
# 1. The basics: publish, then check the subscriber
# ---------------------------------------------------------------------------
@pytest.mark.smoke
def test_registered_event_lets_key_unlock(broker, vehicle):
    broker.publish(TOPIC, make_event("key_registered"))

    assert vehicle.can_unlock("PHONE-JASMIN")


def test_revoked_event_stops_key(broker, vehicle):
    broker.publish(TOPIC, make_event("key_registered"))
    broker.publish(TOPIC, make_event("key_revoked"))

    assert not vehicle.can_unlock("PHONE-JASMIN")


@pytest.mark.negative
def test_events_for_other_vehicles_are_ignored(broker, vehicle):
    broker.publish(TOPIC, make_event("key_registered", vehicle_id="R2-003"))

    assert not vehicle.can_unlock("PHONE-JASMIN")


# ---------------------------------------------------------------------------
# 2. Delay: the effect is NOT there right away
# ---------------------------------------------------------------------------
def test_delayed_event_arrives_eventually():
    slow_broker = InMemoryBroker(delay_s=0.2)
    vehicle = VehicleEventHandler(VEHICLE)
    slow_broker.subscribe(TOPIC, vehicle.handle)

    slow_broker.publish(TOPIC, make_event("key_registered"))

    assert not vehicle.can_unlock("PHONE-JASMIN")            # not delivered yet
    wait_until(lambda: vehicle.can_unlock("PHONE-JASMIN"))   # ... but it will be


def test_wait_until_fails_if_it_never_happens():
    with pytest.raises(AssertionError, match="not met"):
        wait_until(lambda: False, timeout=0.1)


# ---------------------------------------------------------------------------
# 3. YOUR EXERCISES: remove the skip line and write the test body
# ---------------------------------------------------------------------------
def test_duplicate_event_is_handled_once(broker, vehicle):
    event = make_event("key_registered")

    broker.publish(TOPIC, event)
    broker.publish(TOPIC, event)

    assert len(vehicle.processed_ids) == 1
    assert vehicle.can_unlock("PHONE-JASMIN")


# @pytest.mark.skip(reason="Exercise 2")
def test_revoking_unknown_key_does_not_crash(broker, vehicle):
    key_id = "UNKNOWN"
    
    broker.publish(TOPIC, make_event("key_revoked", key_id=key_id))
    
    assert not vehicle.can_unlock(key_id)
    assert vehicle.allowed_keys == set()


def test_unknown_event_type_is_ignored(broker, vehicle):
    unknown_event = make_event("self_destruct")

    broker.publish(TOPIC, unknown_event)

    assert vehicle.ignored == [unknown_event]

    normal_event = make_event("key_registered")
    broker.publish(TOPIC, normal_event)

    assert vehicle.can_unlock("PHONE-JASMIN")


# Exercise 4: out of order. The key_revoked event arrives BEFORE key_registered.
# First decide: should the key be able to unlock afterwards, or not? Why?
# Answer: They key should not be able to unlock. The revoke was the owner's latest intention
# , and it's a security action. When messages arrive out of order, the system should fail safe
# (deny access) rather than open. A revoked key that works again could let a thief or an ex-partner into the car.
# Then write the test that checks your answer, and run it.
# If it fails: is the test wrong, or the code? Write your reasoning here.
# Answer: The code is wrong.
@pytest.mark.xfail(reason="BUG: revoke before register re-enables the key", strict=True)
def test_key_revoked_event_arrives_before_key_registered(broker, vehicle):
    key_revoked_event = make_event("key_revoked")
    key_registered_event = make_event("key_registered")

    broker.publish(TOPIC, key_revoked_event)
    broker.publish(TOPIC, key_registered_event)

    assert vehicle.allowed_keys == set()
    assert vehicle.can_unlock("PHONE-JASMIN")
