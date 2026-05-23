"""Track and summarize port-change frequency over time."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

_DEFAULT_MAX_ENTRIES = 500


@dataclass
class TrendEntry:
    timestamp: str
    added: int
    removed: int
    changed: int

    def total(self) -> int:
        return self.added + self.removed + self.changed


def _entry_to_dict(e: TrendEntry) -> dict:
    return {
        "timestamp": e.timestamp,
        "added": e.added,
        "removed": e.removed,
        "changed": e.changed,
    }


def _entry_from_dict(d: dict) -> TrendEntry:
    return TrendEntry(
        timestamp=d["timestamp"],
        added=int(d.get("added", 0)),
        removed=int(d.get("removed", 0)),
        changed=int(d.get("changed", 0)),
    )


def append_trend_entry(
    path: str | os.PathLike,
    added: int,
    removed: int,
    changed: int,
    max_entries: int = _DEFAULT_MAX_ENTRIES,
) -> TrendEntry:
    """Append a new trend entry to the log file, pruning old entries."""
    p = Path(path)
    entries: List[dict] = []
    if p.exists():
        try:
            entries = json.loads(p.read_text())
        except (json.JSONDecodeError, ValueError):
            entries = []

    entry = TrendEntry(
        timestamp=datetime.now(timezone.utc).isoformat(),
        added=added,
        removed=removed,
        changed=changed,
    )
    entries.append(_entry_to_dict(entry))
    entries = entries[-max_entries:]
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(entries, indent=2))
    return entry


def load_trend_log(path: str | os.PathLike) -> List[TrendEntry]:
    """Load all trend entries from the log file."""
    p = Path(path)
    if not p.exists():
        return []
    try:
        raw = json.loads(p.read_text())
        return [_entry_from_dict(d) for d in raw]
    except (json.JSONDecodeError, ValueError, KeyError):
        return []


def summarize_trend(entries: List[TrendEntry]) -> Dict[str, int]:
    """Return aggregate counts across all entries."""
    return {
        "total_scans": len(entries),
        "total_added": sum(e.added for e in entries),
        "total_removed": sum(e.removed for e in entries),
        "total_changed": sum(e.changed for e in entries),
        "noisy_scans": sum(1 for e in entries if e.total() > 0),
    }
