"""Scan interval scheduler with jitter support for portwatch daemon."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SchedulerConfig:
    """Configuration for the scan scheduler."""
    interval_seconds: int = 60
    jitter_seconds: int = 0
    max_drift_seconds: int = 5


@dataclass
class Scheduler:
    """Tracks when the next scan should fire and handles jitter."""

    config: SchedulerConfig
    _next_run: float = field(init=False)
    _last_run: Optional[float] = field(init=False, default=None)

    def __post_init__(self) -> None:
        self._next_run = time.monotonic()

    def due(self) -> bool:
        """Return True if a scan is due right now."""
        return time.monotonic() >= self._next_run

    def record_run(self) -> None:
        """Call after each scan to schedule the next one."""
        now = time.monotonic()
        self._last_run = now
        jitter = (
            random.uniform(-self.config.jitter_seconds, self.config.jitter_seconds)
            if self.config.jitter_seconds > 0
            else 0.0
        )
        self._next_run = now + self.config.interval_seconds + jitter

    def seconds_until_next(self) -> float:
        """Return seconds remaining until the next scheduled scan (>= 0)."""
        remaining = self._next_run - time.monotonic()
        return max(0.0, remaining)

    def sleep_until_next(self) -> None:
        """Block until the next scan is due."""
        delay = self.seconds_until_next()
        if delay > 0:
            time.sleep(delay)

    @property
    def last_run(self) -> Optional[float]:
        """Monotonic timestamp of the last completed scan, or None."""
        return self._last_run


def make_scheduler(interval: int, jitter: int = 0) -> Scheduler:
    """Convenience factory used by the daemon."""
    cfg = SchedulerConfig(interval_seconds=interval, jitter_seconds=jitter)
    return Scheduler(config=cfg)
