from __future__ import annotations

import time


class CooldownGate:
    def __init__(self, cooldown_seconds: int = 300):
        self.cooldown_seconds = cooldown_seconds
        self._last_sent_at = 0.0

    def allow(self) -> bool:
        now = time.time()
        if now - self._last_sent_at < self.cooldown_seconds:
            return False
        self._last_sent_at = now
        return True
