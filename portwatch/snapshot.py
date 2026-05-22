"""Snapshot management: persist and compare port scan results."""

import json
import logging
from pathlib import Path
from dataclasses import asdict
from typing import Optional

from portwatch.scanner import PortInfo

logger = logging.getLogger(__name__)

DEFAULT_SNAPSHOT_PATH = Path("/var/lib/portwatch/snapshot.json")


def _port_info_from_dict(data: dict) -> PortInfo:
    return PortInfo(
        port=data["port"],
        protocol=data["protocol"],
        service=data.get("service"),
        state=data.get("state", "open"),
    )


def save_snapshot(ports: list[PortInfo], path: Path = DEFAULT_SNAPSHOT_PATH) -> None:
    """Persist a list of PortInfo objects to a JSON snapshot file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [asdict(p) for p in ports]
    path.write_text(json.dumps(payload, indent=2))
    logger.info("Snapshot saved to %s (%d ports)", path, len(ports))


def load_snapshot(path: Path = DEFAULT_SNAPSHOT_PATH) -> Optional[list[PortInfo]]:
    """Load a previously saved snapshot. Returns None if the file does not exist."""
    if not path.exists():
        logger.info("No existing snapshot found at %s", path)
        return None
    try:
        data = json.loads(path.read_text())
        ports = [_port_info_from_dict(entry) for entry in data]
        logger.info("Snapshot loaded from %s (%d ports)", path, len(ports))
        return ports
    except (json.JSONDecodeError, KeyError) as exc:
        logger.error("Failed to parse snapshot at %s: %s", path, exc)
        return None


def diff_snapshots(
    previous: list[PortInfo], current: list[PortInfo]
) -> dict[str, list[PortInfo]]:
    """Compare two snapshots and return appeared/disappeared port sets."""
    prev_set = {(p.port, p.protocol) for p in previous}
    curr_set = {(p.port, p.protocol) for p in current}

    appeared_keys = curr_set - prev_set
    disappeared_keys = prev_set - curr_set

    appeared = [p for p in current if (p.port, p.protocol) in appeared_keys]
    disappeared = [p for p in previous if (p.port, p.protocol) in disappeared_keys]

    return {"appeared": appeared, "disappeared": disappeared}
