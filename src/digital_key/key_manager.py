"""A tiny, simplified model of a vehicle "digital key" system.

This is the code under test for Day 1. It is plain Python with no
dependencies, so you can focus on learning Pytest.

Rules for unlocking a vehicle:
  1. The key must be registered.
  2. The key must not be revoked.
  3. The key must not be expired.
  4. The key must belong to the vehicle being unlocked.
  5. The command must be one of: "unlock", "lock", "open_trunk".
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum


VALID_COMMANDS = {"unlock", "lock", "open_trunk"}


class UnlockResult(str, Enum):
    GRANTED = "granted"
    UNKNOWN_KEY = "unknown_key"
    REVOKED = "revoked"
    EXPIRED = "expired"
    WRONG_VEHICLE = "wrong_vehicle"


class KeyError_(Exception):
    """Raised for invalid input (named with _ to avoid clashing with Python's KeyError)."""


@dataclass
class DigitalKey:
    key_id: str
    vehicle_id: str
    owner: str
    expires_at: datetime
    revoked: bool = False

    def is_expired(self, now: datetime | None = None) -> bool:
        now = now or datetime.now(timezone.utc)
        return now >= self.expires_at


@dataclass
class KeyManager:
    keys: dict[str, DigitalKey] = field(default_factory=dict)

    def register(self, key_id: str, vehicle_id: str, owner: str, valid_days: int = 365) -> DigitalKey:
        if not key_id or not vehicle_id:
            raise KeyError_("key_id and vehicle_id are required")
        if valid_days <= 0:
            raise KeyError_("valid_days must be positive")
        if key_id in self.keys:
            raise KeyError_(f"key {key_id} is already registered")
        key = DigitalKey(
            key_id=key_id,
            vehicle_id=vehicle_id,
            owner=owner,
            expires_at=datetime.now(timezone.utc) + timedelta(days=valid_days),
        )
        self.keys[key_id] = key
        return key

    def revoke(self, key_id: str) -> None:
        if key_id not in self.keys:
            raise KeyError_(f"key {key_id} not found")
        self.keys[key_id].revoked = True

    def keys_for_vehicle(self, vehicle_id: str) -> list[DigitalKey]:
        return [k for k in self.keys.values() if k.vehicle_id == vehicle_id]

    def authorize(self, key_id: str, vehicle_id: str, command: str = "unlock",
                  now: datetime | None = None) -> UnlockResult:
        if command not in VALID_COMMANDS:
            raise KeyError_(f"invalid command: {command}")
        key = self.keys.get(key_id)
        if key is None:
            return UnlockResult.UNKNOWN_KEY
        if key.revoked:
            return UnlockResult.REVOKED
        if key.is_expired(now):
            return UnlockResult.EXPIRED
        if key.vehicle_id != vehicle_id:
            return UnlockResult.WRONG_VEHICLE
        return UnlockResult.GRANTED
