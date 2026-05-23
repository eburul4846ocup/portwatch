"""Severity classification for port change events."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

from portwatch.snapshot import PortDiff


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


# Ports considered high-risk when newly opened
_CRITICAL_PORTS: frozenset[int] = frozenset({
    21,   # FTP
    23,   # Telnet
    445,  # SMB
    3389, # RDP
    5900, # VNC
})

_WARNING_PORTS: frozenset[int] = frozenset({
    22,   # SSH
    3306, # MySQL
    5432, # PostgreSQL
    6379, # Redis
    27017,# MongoDB
})


@dataclass(frozen=True)
class SeverityReport:
    severity: Severity
    reasons: List[str]

    def as_dict(self) -> Dict:
        return {"severity": self.severity.value, "reasons": self.reasons}


def classify_diff(diff: PortDiff) -> SeverityReport:
    """Return the highest applicable severity for a PortDiff."""
    reasons: List[str] = []
    level = Severity.INFO

    for port_info in diff.added:
        if port_info.port in _CRITICAL_PORTS:
            reasons.append(
                f"Critical port {port_info.port}/{port_info.proto} opened"
            )
            level = Severity.CRITICAL
        elif port_info.port in _WARNING_PORTS:
            reasons.append(
                f"Sensitive port {port_info.port}/{port_info.proto} opened"
            )
            if level != Severity.CRITICAL:
                level = Severity.WARNING
        else:
            reasons.append(
                f"New port {port_info.port}/{port_info.proto} opened"
            )

    for port_info in diff.removed:
        reasons.append(
            f"Port {port_info.port}/{port_info.proto} closed"
        )
        if level == Severity.INFO:
            level = Severity.WARNING

    return SeverityReport(severity=level, reasons=reasons)
