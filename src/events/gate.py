from __future__ import annotations

import time


class CooldownGate:
    def __init__(self, cooldown_seconds: int = 300):
        self.cooldown_seconds = cooldown_seconds
        self._last_sent_at_by_key: dict[str, float] = {}

    def allow(self, key: str = "default") -> bool:
        now = time.time()
        last = self._last_sent_at_by_key.get(key, 0.0)
        if now - last < self.cooldown_seconds:
            return False
        self._last_sent_at_by_key[key] = now
        return True
