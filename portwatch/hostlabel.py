"""Host label store — attach human-readable names/roles to IP addresses."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

# Stored as { "<ip>": {"label": str, "role": str | null} }
_LabelMap = Dict[str, dict]


def load_labels(path: Path) -> _LabelMap:
    """Load label map from *path*; return empty dict if missing or corrupt."""
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
        if not isinstance(data, dict):
            return {}
        return data
    except (json.JSONDecodeError, OSError):
        return {}


def save_labels(path: Path, labels: _LabelMap) -> None:
    """Persist *labels* to *path*, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(labels, indent=2))


def set_label(path: Path, ip: str, label: str, role: Optional[str] = None) -> None:
    """Add or update the label (and optional role) for *ip*."""
    labels = load_labels(path)
    labels[ip] = {"label": label, "role": role}
    save_labels(path, labels)


def remove_label(path: Path, ip: str) -> bool:
    """Remove the entry for *ip*. Returns True if it existed."""
    labels = load_labels(path)
    if ip not in labels:
        return False
    del labels[ip]
    save_labels(path, labels)
    return True


def get_label(path: Path, ip: str) -> Optional[dict]:
    """Return the label dict for *ip*, or None if not found."""
    return load_labels(path).get(ip)


def list_labels(path: Path) -> list[tuple[str, str, Optional[str]]]:
    """Return sorted list of (ip, label, role) tuples."""
    labels = load_labels(path)
    return [
        (ip, entry.get("label", ""), entry.get("role"))
        for ip, entry in sorted(labels.items())
    ]
