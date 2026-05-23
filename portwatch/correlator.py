"""correlator.py – Cross-reference open ports against known CVE/advisory data.

Keeps a lightweight local advisory index (JSON) and returns matches for any
list of PortInfo objects so callers can surface potential vulnerabilities.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from portwatch.scanner import PortInfo

log = logging.getLogger(__name__)

_DEFAULT_DB = Path(__file__).parent / "data" / "advisories.json"


@dataclass
class Advisory:
    cve_id: str
    port: int
    proto: str
    service: str
    description: str
    severity: str = "medium"  # low | medium | high | critical

    def as_dict(self) -> dict:
        return {
            "cve_id": self.cve_id,
            "port": self.port,
            "proto": self.proto,
            "service": self.service,
            "description": self.description,
            "severity": self.severity,
        }


@dataclass
class CorrelationReport:
    matches: List[dict] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {"matches": self.matches}

    @property
    def has_findings(self) -> bool:
        return bool(self.matches)


def _load_advisories(db_path: Path) -> List[Advisory]:
    if not db_path.exists():
        log.debug("Advisory DB not found at %s", db_path)
        return []
    try:
        raw = json.loads(db_path.read_text())
        if not isinstance(raw, list):
            log.warning("Advisory DB is not a list – skipping")
            return []
        return [
            Advisory(
                cve_id=e.get("cve_id", "UNKNOWN"),
                port=int(e["port"]),
                proto=e.get("proto", "tcp"),
                service=e.get("service", ""),
                description=e.get("description", ""),
                severity=e.get("severity", "medium"),
            )
            for e in raw
            if "port" in e
        ]
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        log.error("Failed to parse advisory DB: %s", exc)
        return []


def correlate(
    ports: List[PortInfo],
    db_path: Optional[Path] = None,
) -> CorrelationReport:
    """Return advisories that match any port in *ports*."""
    db_path = db_path or _DEFAULT_DB
    advisories = _load_advisories(db_path)
    report = CorrelationReport()
    for port_info in ports:
        for adv in advisories:
            if adv.port == port_info.port and adv.proto == port_info.proto:
                report.matches.append(
                    {"port_info": str(port_info), **adv.as_dict()}
                )
    return report
