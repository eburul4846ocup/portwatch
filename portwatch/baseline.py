"""Baseline management: approve current ports as the expected state."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Optional

from portwatch.scanner import PortInfo
from portwatch.snapshot import save_snapshot, load_snapshot

logger = logging.getLogger(__name__)

DEFAULT_BASELINE_PATH = Path("portwatch_baseline.json")


def save_baseline(ports: List[PortInfo], path: Path = DEFAULT_BASELINE_PATH) -> None:
    """Persist *ports* as the approved baseline."""
    save_snapshot(ports, path)
    logger.info("Baseline saved to %s (%d ports)", path, len(ports))


def load_baseline(path: Path = DEFAULT_BASELINE_PATH) -> Optional[List[PortInfo]]:
    """Load the approved baseline, returning *None* if it does not exist."""
    ports = load_snapshot(path)
    if ports is None:
        logger.debug("No baseline found at %s", path)
    else:
        logger.debug("Loaded baseline from %s (%d ports)", path, len(ports))
    return ports


def baseline_exists(path: Path = DEFAULT_BASELINE_PATH) -> bool:
    """Return True if a baseline file exists at *path*."""
    return path.exists()


def approve_ports(
    ports: List[PortInfo],
    path: Path = DEFAULT_BASELINE_PATH,
    comment: str = "",
) -> None:
    """Save *ports* as the new baseline, optionally recording a *comment*."""
    save_baseline(ports, path)
    if comment:
        meta_path = path.with_suffix(".meta.json")
        meta_path.write_text(json.dumps({"comment": comment}), encoding="utf-8")
        logger.debug("Baseline comment written to %s", meta_path)


def read_baseline_comment(path: Path = DEFAULT_BASELINE_PATH) -> str:
    """Return the comment stored alongside the baseline, or an empty string."""
    meta_path = path.with_suffix(".meta.json")
    if not meta_path.exists():
        return ""
    try:
        data = json.loads(meta_path.read_text(encoding="utf-8"))
        return data.get("comment", "")
    except (json.JSONDecodeError, OSError):
        return ""
