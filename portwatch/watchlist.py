"""Watchlist: define ports that must always be open or must never be open."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from portwatch.scanner import PortInfo


@dataclass
class WatchlistEntry:
    port: int
    protocol: str = "tcp"
    required: bool = True   # True = must be open; False = must be closed
    label: Optional[str] = None


@dataclass
class WatchlistViolation:
    entry: WatchlistEntry
    actual_port: Optional[PortInfo]
    message: str


def _entry_from_dict(d: dict) -> WatchlistEntry:
    return WatchlistEntry(
        port=int(d["port"]),
        protocol=d.get("protocol", "tcp"),
        required=bool(d.get("required", True)),
        label=d.get("label"),
    )


def load_watchlist(path: Path) -> List[WatchlistEntry]:
    """Load watchlist entries from a JSON file. Returns empty list if missing."""
    if not path.exists():
        return []
    with path.open() as fh:
        data = json.load(fh)
    return [_entry_from_dict(item) for item in data.get("watchlist", [])]


def save_watchlist(path: Path, entries: List[WatchlistEntry]) -> None:
    """Persist watchlist entries to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {
            "port": e.port,
            "protocol": e.protocol,
            "required": e.required,
            "label": e.label,
        }
        for e in entries
    ]
    with path.open("w") as fh:
        json.dump({"watchlist": payload}, fh, indent=2)


def check_watchlist(
    entries: List[WatchlistEntry], open_ports: List[PortInfo]
) -> List[WatchlistViolation]:
    """Return violations: required ports that are closed, or forbidden ports that are open."""
    open_index = {(p.port, p.protocol): p for p in open_ports}
    violations: List[WatchlistViolation] = []

    for entry in entries:
        key = (entry.port, entry.protocol)
        present = open_index.get(key)
        if entry.required and present is None:
            violations.append(
                WatchlistViolation(
                    entry=entry,
                    actual_port=None,
                    message=f"Required port {entry.port}/{entry.protocol} is not open",
                )
            )
        elif not entry.required and present is not None:
            violations.append(
                WatchlistViolation(
                    entry=entry,
                    actual_port=present,
                    message=f"Forbidden port {entry.port}/{entry.protocol} is open",
                )
            )
    return violations
