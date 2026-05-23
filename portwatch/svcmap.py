"""Service name mapping: resolve well-known port numbers to human-readable names."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Built-in fallback map for the most common ports
_BUILTIN: Dict[str, str] = {
    "tcp:21": "FTP",
    "tcp:22": "SSH",
    "tcp:23": "Telnet",
    "tcp:25": "SMTP",
    "tcp:53": "DNS",
    "tcp:80": "HTTP",
    "tcp:110": "POP3",
    "tcp:143": "IMAP",
    "tcp:443": "HTTPS",
    "tcp:3306": "MySQL",
    "tcp:5432": "PostgreSQL",
    "tcp:6379": "Redis",
    "tcp:8080": "HTTP-Alt",
    "tcp:8443": "HTTPS-Alt",
    "tcp:27017": "MongoDB",
}


def _port_key(proto: str, port: int) -> str:
    return f"{proto.lower()}:{port}"


def load_svcmap(path: Path) -> Dict[str, str]:
    """Load a custom service map from *path*; returns empty dict if missing."""
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
        if not isinstance(data, dict):
            logger.warning("svcmap file %s is not a JSON object – ignored", path)
            return {}
        return {str(k): str(v) for k, v in data.items()}
    except json.JSONDecodeError as exc:
        logger.warning("svcmap file %s contains invalid JSON: %s", path, exc)
        return {}


def save_svcmap(path: Path, svcmap: Dict[str, str]) -> None:
    """Persist *svcmap* to *path* as pretty-printed JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(svcmap, indent=2, sort_keys=True))


def set_service(path: Path, proto: str, port: int, name: str) -> Dict[str, str]:
    """Add or update a service name entry and save."""
    svcmap = load_svcmap(path)
    svcmap[_port_key(proto, port)] = name
    save_svcmap(path, svcmap)
    return svcmap


def remove_service(path: Path, proto: str, port: int) -> bool:
    """Remove an entry; returns True if it existed."""
    svcmap = load_svcmap(path)
    key = _port_key(proto, port)
    if key not in svcmap:
        return False
    del svcmap[key]
    save_svcmap(path, svcmap)
    return True


def lookup(proto: str, port: int, custom: Optional[Dict[str, str]] = None) -> Optional[str]:
    """Return a human-readable service name, checking *custom* map first."""
    key = _port_key(proto, port)
    if custom and key in custom:
        return custom[key]
    return _BUILTIN.get(key)
