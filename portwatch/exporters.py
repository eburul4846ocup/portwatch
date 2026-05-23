"""Export port snapshots and diffs to various formats (CSV, JSON lines, HTML)."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import List

from portwatch.scanner import PortInfo
from portwatch.snapshot import PortDiff


def export_ports_csv(ports: List[PortInfo]) -> str:
    """Return a CSV string for a list of PortInfo objects."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["port", "proto", "state", "service", "address"])
    for p in ports:
        writer.writerow([p.port, p.proto, p.state, p.service, p.address])
    return buf.getvalue()


def export_ports_jsonl(ports: List[PortInfo]) -> str:
    """Return newline-delimited JSON, one object per port."""
    lines = []
    for p in ports:
        lines.append(json.dumps({
            "port": p.port,
            "proto": p.proto,
            "state": p.state,
            "service": p.service,
            "address": p.address,
        }))
    return "\n".join(lines)


def export_diff_html(diff: PortDiff, title: str = "Port Diff Report") -> str:
    """Return a minimal HTML report for a PortDiff."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    def _rows(ports: List[PortInfo], css_class: str) -> str:
        rows = []
        for p in ports:
            rows.append(
                f'<tr class="{css_class}">'
                f"<td>{p.port}</td><td>{p.proto}</td>"
                f"<td>{p.state}</td><td>{p.service}</td>"
                f"<td>{p.address}</td></tr>"
            )
        return "\n".join(rows)

    added_rows = _rows(diff.added, "added")
    removed_rows = _rows(diff.removed, "removed")
    changed_rows = _rows([new for _, new in diff.changed], "changed")

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{title}</title>
<style>
body{{font-family:monospace;padding:1em}}
table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ccc;padding:4px 8px}}
th{{background:#eee}}
tr.added{{background:#d4edda}}
tr.removed{{background:#f8d7da}}
tr.changed{{background:#fff3cd}}
</style></head><body>
<h2>{title}</h2><p>Generated: {ts}</p>
<table><thead><tr><th>Port</th><th>Proto</th><th>State</th><th>Service</th><th>Address</th></tr></thead>
<tbody>
{added_rows}
{removed_rows}
{changed_rows}
</tbody></table>
</body></html>
"""
