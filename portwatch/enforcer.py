"""Enforcer: compare a live scan against the approved baseline."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional, Tuple

from portwatch.scanner import PortInfo, scan_ports
from portwatch.snapshot import PortDiff, compute_diff
from portwatch.baseline import (
    load_baseline,
    baseline_exists,
    DEFAULT_BASELINE_PATH,
)

logger = logging.getLogger(__name__)


class BaselineMissingError(RuntimeError):
    """Raised when enforcement is requested but no baseline exists."""


def enforce(
    baseline_path: Path = DEFAULT_BASELINE_PATH,
    ports: Optional[List[PortInfo]] = None,
) -> Tuple[PortDiff, bool]:
    """Compare *ports* (or a fresh scan) against the baseline.

    Returns ``(diff, compliant)`` where *compliant* is True when there are no
    unexpected additions or removals.

    Raises :class:`BaselineMissingError` if no baseline file is found.
    """
    if not baseline_exists(baseline_path):
        raise BaselineMissingError(
            f"No baseline found at '{baseline_path}'. "
            "Run 'portwatch approve' first."
        )

    baseline = load_baseline(baseline_path) or []
    current = ports if ports is not None else scan_ports()

    diff = compute_diff(baseline, current)
    compliant = not diff.added and not diff.removed

    if compliant:
        logger.info("Host is compliant with baseline.")
    else:
        logger.warning(
            "Compliance violation: +%d added, -%d removed",
            len(diff.added),
            len(diff.removed),
        )

    return diff, compliant
