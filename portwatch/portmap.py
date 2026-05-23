"""portmap.py — Maintain a human-readable map of port→description overrides.

Allows operators to annotate ports with custom service names that override
the auto-resolved service names produced by scanner.resolve_service.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Optional

log = logging.getLogger(__name__)

# key format: "<port>/<proto>"  e.g. "8080/tcp"
_PortMapData = Dict[str, str]


def _port_key(port: int, proto: str) -> str:
    return f"{port}/{proto.lower()}"


def load_portmap(path: Path) -> _PortMapData:
    """Load port descriptions from *path*; return empty dict if missing."""
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
        if not isinstance(data, dict):
            log.warning("portmap file %s is not a JSON object — ignoring", path)
            return {}
        return {k: str(v) for k, v in data.items()}
    except json.JSONDecodeError as exc:
        log.warning("portmap file %s contains invalid JSON: %s", path, exc)
        return {}


def save_portmap(path: Path, data: _PortMapData) -> None:
    """Persist *data* to *path*, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True))


def set_description(path: Path, port: int, proto: str, description: str) -> None:
    """Add or update the description for *port*/*proto*."""
    data = load_portmap(path)
    data[_port_key(port, proto)] = description
    save_portmap(path, data)
    log.debug("portmap: set %s/%s = %r", port, proto, description)


def remove_description(path: Path, port: int, proto: str) -> bool:
    """Remove the description for *port*/*proto*.  Returns True if it existed."""
    data = load_portmap(path)
    key = _port_key(port, proto)
    if key not in data:
        return False
    del data[key]
    save_portmap(path, data)
    log.debug("portmap: removed %s", key)
    return True


def lookup(data: _PortMapData, port: int, proto: str) -> Optional[str]:
    """Return the custom description for *port*/*proto*, or None."""
    return data.get(_port_key(port, proto))
