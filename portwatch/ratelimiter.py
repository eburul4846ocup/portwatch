"""Rate limiting for alerts to prevent notification storms."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

_DEFAULT_STATE_FILE = "/var/lib/portwatch/ratelimit_state.json"
_DEFAULT_COOLDOWN = 300  # seconds


@dataclass
class RateLimitConfig:
    cooldown_seconds: int = _DEFAULT_COOLDOWN
    state_file: str = _DEFAULT_STATE_FILE


@dataclass
class RateLimiter:
    config: RateLimitConfig
    _state: Dict[str, float] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self._load_state()

    def _load_state(self) -> None:
        path = Path(self.config.state_file)
        if path.exists():
            try:
                self._state = json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                self._state = {}
        else:
            self._state = {}

    def _save_state(self) -> None:
        path = Path(self.config.state_file)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(self._state))
        except OSError:
            pass

    def is_allowed(self, key: str) -> bool:
        """Return True if the alert for *key* is not currently suppressed."""
        last = self._state.get(key)
        if last is None:
            return True
        return (time.time() - last) >= self.config.cooldown_seconds

    def record(self, key: str) -> None:
        """Mark *key* as having fired right now."""
        self._state[key] = time.time()
        self._save_state()

    def reset(self, key: Optional[str] = None) -> None:
        """Clear rate-limit state for *key*, or all keys if None."""
        if key is None:
            self._state.clear()
        else:
            self._state.pop(key, None)
        self._save_state()
