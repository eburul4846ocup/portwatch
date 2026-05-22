"""Snapshot persistence and diffing for portwatch."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from portwatch.scanner import PortInfo


def _port_info_from_dict(d: dict) -> PortInfo:
    return PortInfo(
        port=d["port"],
        protocol=d["protocol"],
        service=d.get("service"),
        state=d.get("state", "open"),
    )


def save_snapshot(ports: List[PortInfo], path: Path) -> None:
    """Persist a list of PortInfo objects to *path* as JSON."""
    data = [
        {
            "port": p.port,
            "protocol": p.protocol,
            "service": p.service,
            "state": p.state,
        }
        for p in ports
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def load_snapshot(path: Path) -> Optional[List[PortInfo]]:
    """Load a snapshot from *path*.  Returns None if the file is absent."""
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return [_port_info_from_dict(d) for d in data]
    except (json.JSONDecodeError, KeyError):
        return None


@dataclass
class PortDiff:
    added: List[PortInfo]
    removed: List[PortInfo]

    def has_changes(self) -> bool:
        return bool(self.added or self.removed)


def diff_snapshots(
    old: List[PortInfo], new: List[PortInfo]
) -> PortDiff:
    """Return ports that were added or removed between two snapshots."""

    def key(p: PortInfo) -> tuple:
        return (p.port, p.protocol)

    old_map: Dict[tuple, PortInfo] = {key(p): p for p in old}
    new_map: Dict[tuple, PortInfo] = {key(p): p for p in new}

    added = [new_map[k] for k in new_map if k not in old_map]
    removed = [old_map[k] for k in old_map if k not in new_map]
    return PortDiff(added=added, removed=removed)
