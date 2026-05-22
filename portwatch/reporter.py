"""Human-readable report generation for port scan results."""

from __future__ import annotations

import json
from datetime import datetime
from typing import List

from portwatch.scanner import PortInfo
from portwatch.snapshot import PortDiff


def _format_port_row(info: PortInfo) -> str:
    service = info.service or "unknown"
    return f"  {info.port:<6} {info.proto:<5} {info.state:<8} {service}"


def format_port_table(ports: List[PortInfo]) -> str:
    """Return a formatted table of open ports."""
    if not ports:
        return "  (no open ports)"
    header = f"  {'PORT':<6} {'PROTO':<5} {'STATE':<8} SERVICE"
    separator = "  " + "-" * 40
    rows = [_format_port_row(p) for p in sorted(ports, key=lambda p: p.port)]
    return "\n".join([header, separator] + rows)


def format_diff_report(diff: PortDiff, timestamp: datetime | None = None) -> str:
    """Return a human-readable diff report."""
    ts = timestamp or datetime.utcnow()
    lines: List[str] = [
        f"PortWatch Diff Report — {ts.strftime('%Y-%m-%d %H:%M:%S')} UTC",
        "=" * 55,
    ]

    if diff.added:
        lines.append(f"\nNEW ports ({len(diff.added)}):")
        for p in sorted(diff.added, key=lambda p: p.port):
            lines.append(f"  [+] {p.port}/{p.proto}  {p.service or 'unknown'}")

    if diff.removed:
        lines.append(f"\nREMOVED ports ({len(diff.removed)}):")
        for p in sorted(diff.removed, key=lambda p: p.port):
            lines.append(f"  [-] {p.port}/{p.proto}  {p.service or 'unknown'}")

    if not diff.added and not diff.removed:
        lines.append("\nNo changes detected.")

    return "\n".join(lines)


def format_json_report(
    ports: List[PortInfo],
    timestamp: datetime | None = None,
) -> str:
    """Return a JSON-serialisable snapshot report as a string."""
    ts = timestamp or datetime.utcnow()
    payload = {
        "generated_at": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "port_count": len(ports),
        "ports": [
            {
                "port": p.port,
                "proto": p.proto,
                "state": p.state,
                "service": p.service,
            }
            for p in sorted(ports, key=lambda p: p.port)
        ],
    }
    return json.dumps(payload, indent=2)
