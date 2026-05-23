"""CLI command: portwatch severity — show severity classification for current diff."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from portwatch.scanner import scan_ports
from portwatch.snapshot import load_snapshot, diff_snapshots
from portwatch.severity import classify_diff, Severity


def _default_snapshot_path() -> str:
    return str(Path.home() / ".portwatch" / "snapshot.json")


def cmd_severity(ns: argparse.Namespace) -> None:
    """Scan current ports, diff against snapshot, and report severity."""
    snapshot_path = Path(ns.snapshot)

    baseline = load_snapshot(snapshot_path)
    if baseline is None:
        print("No snapshot found. Run 'portwatch scan' first.", file=sys.stderr)
        sys.exit(1)

    current = scan_ports()
    diff = diff_snapshots(baseline, current)

    if not diff.added and not diff.removed:
        if ns.format == "json":
            print(json.dumps({"severity": "info", "reasons": [], "changes": False}))
        else:
            print("[INFO] No changes detected.")
        sys.exit(0)

    report = classify_diff(diff)

    if ns.format == "json":
        data = report.as_dict()
        data["changes"] = True
        print(json.dumps(data, indent=2))
    else:
        label_color = {
            Severity.INFO: "",
            Severity.WARNING: "\033[33m",
            Severity.CRITICAL: "\033[31m",
        }
        reset = "\033[0m"
        color = label_color.get(report.severity, "")
        print(f"{color}[{report.severity.value.upper()}]{reset} Port changes detected:")
        for reason in report.reasons:
            print(f"  - {reason}")

    if report.severity == Severity.CRITICAL:
        sys.exit(2)
    elif report.severity == Severity.WARNING:
        sys.exit(1)
    else:
        sys.exit(0)


def register_severity_commands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "severity",
        help="Classify severity of port changes against last snapshot",
    )
    p.add_argument(
        "--snapshot",
        default=_default_snapshot_path(),
        help="Path to snapshot file",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    p.set_defaults(func=cmd_severity)
