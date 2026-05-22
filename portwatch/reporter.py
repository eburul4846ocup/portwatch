"""Formatting helpers for port scan results and diffs."""

from __future__ import annotations

import json
from typing import List

from portwatch.scanner import PortInfo
from portwatch.snapshot import PortDiff

_COL_WIDTHS = (7, 8, 20, 10)
_HEADERS = ("PORT", "PROTO", "SERVICE", "STATE")


def _format_port_row(port: PortInfo) -> str:
    return (
        f"{port.port:<{_COL_WIDTHS[0]}}"
        f"{port.proto:<{_COL_WIDTHS[1]}}"
        f"{port.service:<{_COL_WIDTHS[2]}}"
        f"{port.state:<{_COL_WIDTHS[3]}}"
    )


def format_port_table(ports: List[PortInfo]) -> str:
    """Return a human-readable table of open ports."""
    header = (
        f"{_HEADERS[0]:<{_COL_WIDTHS[0]}}"
        f"{_HEADERS[1]:<{_COL_WIDTHS[1]}}"
        f"{_HEADERS[2]:<{_COL_WIDTHS[2]}}"
        f"{_HEADERS[3]:<{_COL_WIDTHS[3]}}"
    )
    separator = "-" * sum(_COL_WIDTHS)
    if not ports:
        return f"{header}\n{separator}\n(no open ports)"
    rows = [_format_port_row(p) for p in sorted(ports, key=lambda p: p.port)]
    return "\n".join([header, separator] + rows)


def format_diff_report(diff: PortDiff) -> str:
    """Return a human-readable summary of port changes."""
    lines: List[str] = []
    if diff.added:
        lines.append("ADDED ports:")
        for p in sorted(diff.added, key=lambda p: p.port):
            lines.append(f"  + {p.port}/{p.proto}  {p.service}")
    if diff.removed:
        lines.append("REMOVED ports:")
        for p in sorted(diff.removed, key=lambda p: p.port):
            lines.append(f"  - {p.port}/{p.proto}  {p.service}")
    if diff.changed:
        lines.append("CHANGED ports:")
        for old, new in sorted(diff.changed, key=lambda t: t[0].port):
            lines.append(f"  ~ {old.port}/{old.proto}  {old.service!r} -> {new.service!r}")
    if not lines:
        return "No changes detected."
    return "\n".join(lines)


def format_json_report(ports: List[PortInfo]) -> str:
    """Return a JSON-serialisable string of port info."""
    data = [
        {"port": p.port, "proto": p.proto, "service": p.service, "state": p.state}
        for p in sorted(ports, key=lambda p: p.port)
    ]
    return json.dumps(data, indent=2)


def format_history_summary(entries: List[dict]) -> str:
    """Return a compact summary of historical scan entries."""
    if not entries:
        return "No history available."
    lines = [f"{'TIMESTAMP':<26} {'OPEN PORTS':>10}"]
    lines.append("-" * 38)
    for entry in entries:
        ts = entry["timestamp"].isoformat(timespec="seconds")
        count = len(entry["ports"])
        lines.append(f"{ts:<26} {count:>10}")
    return "\n".join(lines)
