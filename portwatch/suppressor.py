"""Suppressor: temporarily silence alerts for known ports or time windows."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from portwatch.scanner import PortInfo


@dataclass
class SuppressionRule:
    port: int
    proto: str  # 'tcp' or 'udp'
    reason: str
    expires_at: Optional[str] = None  # ISO-8601 string or None (permanent)

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        expiry = datetime.fromisoformat(self.expires_at)
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        return datetime.now(tz=timezone.utc) > expiry

    def matches(self, port_info: PortInfo) -> bool:
        return (
            self.port == port_info.port
            and self.proto == port_info.proto
            and not self.is_expired()
        )


@dataclass
class Suppressor:
    rules: List[SuppressionRule] = field(default_factory=list)

    def is_suppressed(self, port_info: PortInfo) -> bool:
        return any(r.matches(port_info) for r in self.rules)

    def active_rules(self) -> List[SuppressionRule]:
        return [r for r in self.rules if not r.is_expired()]


def _rule_from_dict(d: dict) -> SuppressionRule:
    return SuppressionRule(
        port=int(d["port"]),
        proto=d["proto"],
        reason=d.get("reason", ""),
        expires_at=d.get("expires_at"),
    )


def load_suppressions(path: str) -> Suppressor:
    """Load suppression rules from a JSON file. Returns empty Suppressor if missing."""
    if not os.path.exists(path):
        return Suppressor()
    with open(path, "r") as fh:
        data = json.load(fh)
    rules = [_rule_from_dict(item) for item in data.get("suppressions", [])]
    return Suppressor(rules=rules)


def save_suppressions(path: str, suppressor: Suppressor) -> None:
    """Persist suppression rules to a JSON file."""
    data = {
        "suppressions": [
            {
                "port": r.port,
                "proto": r.proto,
                "reason": r.reason,
                "expires_at": r.expires_at,
            }
            for r in suppressor.rules
        ]
    }
    with open(path, "w") as fh:
        json.dump(data, fh, indent=2)
