"""Manages historical port scan records for trend analysis."""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import List, Optional

from portwatch.scanner import PortInfo

HISTORY_VERSION = 1


def _port_info_to_dict(port: PortInfo) -> dict:
    return {
        "port": port.port,
        "proto": port.proto,
        "service": port.service,
        "state": port.state,
    }


def _port_info_from_dict(d: dict) -> PortInfo:
    return PortInfo(
        port=d["port"],
        proto=d["proto"],
        service=d.get("service", ""),
        state=d.get("state", "open"),
    )


def append_history_entry(
    history_path: str,
    ports: List[PortInfo],
    timestamp: Optional[datetime] = None,
) -> None:
    """Append a scan result entry to the history file."""
    if timestamp is None:
        timestamp = datetime.utcnow()

    entry = {
        "version": HISTORY_VERSION,
        "timestamp": timestamp.isoformat(),
        "ports": [_port_info_to_dict(p) for p in ports],
    }

    os.makedirs(os.path.dirname(history_path) or ".", exist_ok=True)
    with open(history_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def load_history(
    history_path: str,
    limit: Optional[int] = None,
) -> List[dict]:
    """Load history entries from a JSONL file, newest last.

    Returns a list of dicts with keys 'timestamp' (datetime) and
    'ports' (List[PortInfo]).
    """
    if not os.path.exists(history_path):
        return []

    entries: List[dict] = []
    with open(history_path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
                entries.append({
                    "timestamp": datetime.fromisoformat(raw["timestamp"]),
                    "ports": [_port_info_from_dict(p) for p in raw.get("ports", [])],
                })
            except (json.JSONDecodeError, KeyError, ValueError):
                continue

    if limit is not None:
        entries = entries[-limit:]
    return entries
