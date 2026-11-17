"""Small local abuse limits; edge DDoS mitigation still belongs upstream."""

import threading
import time


class SlidingWindowLimiter:
    def __init__(self, maximum: int, window_seconds: int):
        self.maximum = maximum
        self.window_seconds = window_seconds
        self._events: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        with self._lock:
            # Bound memory even if many different clients connect.
            if len(self._events) > 1024:
                self._events = {
                    client: times for client, times in self._events.items()
                    if times and times[-1] > now - self.window_seconds
                }
            if key not in self._events and len(self._events) >= 1024:
                return False
            recent = [event for event in self._events.get(key, []) if event > now - self.window_seconds]
            if len(recent) >= self.maximum:
                self._events[key] = recent
                return False
            recent.append(now)
            self._events[key] = recent
            return True
