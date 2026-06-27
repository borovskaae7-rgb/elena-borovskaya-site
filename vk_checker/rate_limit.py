from __future__ import annotations

import asyncio
import random
import threading
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class LimitConfig:
    rpm: int
    jitter_ms: int = 250


class AsyncRateLimiter:
    def __init__(self, config: LimitConfig) -> None:
        self.delay = 60 / max(config.rpm, 1)
        self.jitter = max(config.jitter_ms, 0) / 1000
        self._lock = asyncio.Lock()
        self._last = 0.0

    async def wait(self) -> None:
        async with self._lock:
            loop = asyncio.get_running_loop()
            now = loop.time()
            wait_for = self.delay - (now - self._last) + random.uniform(0, self.jitter)
            if wait_for > 0:
                await asyncio.sleep(wait_for)
            self._last = loop.time()


class SyncRateLimiter:
    def __init__(self, config: LimitConfig) -> None:
        self.delay = 60 / max(config.rpm, 1)
        self.jitter = max(config.jitter_ms, 0) / 1000
        self._lock = threading.Lock()
        self._last = 0.0

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            wait_for = self.delay - (now - self._last) + random.uniform(0, self.jitter)
            if wait_for > 0:
                time.sleep(wait_for)
            self._last = time.monotonic()
