"""CLI sub-commands for exporting port data."""

from __future__ import annotations

import argparse
import sys

from portwatch.exporters import export_diff_html, export_ports_csv, export_ports_jsonl
from portwatch.snapshot import load_snapshot, diff_snapshots


def _snapshot_path(args: argparse.Namespace) -> str:
    return getattr(args, "snapshot", "portwatch_snapshot.json")


def cmd_export_ports(args: argparse.Namespace) -> int:
    """Export the current snapshot in the requested format."""
    ports = load_snapshot(_snapshot_path(args))
    if ports is None:
        print("No snapshot found.", file=sys.stderr)
        return 1

    fmt = args.format.lower()
    if fmt == "csv":
        print(export_ports_csv(ports))
    elif fmt == "jsonl":
        print(export_ports_jsonl(ports))
    else:
        print(f"Unknown format: {fmt}", file=sys.stderr)
        return 1
    return 0


def cmd_export_diff(args: argparse.Namespace) -> int:
    """Export a diff between two snapshots as HTML."""
    before = load_snapshot(args.before)
    after = load_snapshot(args.after)

    if before is None:
        print(f"Cannot load snapshot: {args.before}", file=sys.stderr)
        return 1
    if after is None:
        print(f"Cannot load snapshot: {args.after}", file=sys.stderr)
        return 1

    diff = diff_snapshots(before, after)
    html = export_diff_html(diff, title=f"Diff: {args.before} → {args.after}")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(html)
        print(f"Report written to {args.output}")
    else:
        print(html)
    return 0


def register_exporter_commands(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p_exp = sub.add_parser("export", help="Export snapshot data")
    p_exp.add_argument("--snapshot", default="portwatch_snapshot.json")
    p_exp.add_argument("--format", choices=["csv", "jsonl"], default="csv")
    p_exp.set_defaults(func=cmd_export_ports)

    p_diff = sub.add_parser("export-diff", help="Export diff between two snapshots as HTML")
    p_diff.add_argument("before", help="Path to the older snapshot file")
    p_diff.add_argument("after", help="Path to the newer snapshot file")
    p_diff.add_argument("--output", "-o", default="", help="Write HTML to file instead of stdout")
    p_diff.set_defaults(func=cmd_export_diff)
