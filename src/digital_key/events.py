"""Day 3: a tiny in-memory Pub/Sub broker and a vehicle that listens to key events.

Real systems use Google Pub/Sub, Kafka or MQTT. This broker has no network and
no cloud account, but it behaves like one in the ways that matter for testing:
  - publishers and subscribers never talk directly, only through a topic
  - delivery can be delayed (delay_s), so the effect is not there right away
  - the same message can be delivered more than once (publish it twice)
"""

import threading
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class KeyEvent:
    message_id: str   # unique per message; the same id twice means a duplicate
    event_type: str   # "key_registered" or "key_revoked"
    key_id: str
    vehicle_id: str


Handler = Callable[[KeyEvent], None]


class InMemoryBroker:
    def __init__(self, delay_s: float = 0.0):
        self.delay_s = delay_s
        self._subscribers: dict[str, list[Handler]] = defaultdict(list)

    def subscribe(self, topic: str, handler: Handler) -> None:
        self._subscribers[topic].append(handler)

    def publish(self, topic: str, event: KeyEvent) -> None:
        for handler in self._subscribers[topic]:
            if self.delay_s == 0:
                handler(event)
            else:
                # Deliver later, on another thread, like a real broker would.
                timer = threading.Timer(self.delay_s, handler, args=[event])
                timer.daemon = True
                timer.start()


class VehicleEventHandler:
    """The vehicle's side: keeps its own set of keys that may unlock it."""

    def __init__(self, vehicle_id: str):
        self.vehicle_id = vehicle_id
        self.allowed_keys: set[str] = set()
        self.processed_ids: list[str] = []   # message ids actually handled, in order
        self.ignored: list[KeyEvent] = []     # events we could not use
        self._lock = threading.Lock()

    def handle(self, event: KeyEvent) -> None:
        with self._lock:
            if event.vehicle_id != self.vehicle_id:
                return
            if event.message_id in self.processed_ids:
                return  # duplicate delivery: already handled, do nothing
            if event.event_type == "key_registered":
                self.allowed_keys.add(event.key_id)
            elif event.event_type == "key_revoked":
                self.allowed_keys.discard(event.key_id)
            else:
                self.ignored.append(event)
                return
            self.processed_ids.append(event.message_id)

    def can_unlock(self, key_id: str) -> bool:
        with self._lock:
            return key_id in self.allowed_keys
