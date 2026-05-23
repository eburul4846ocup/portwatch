"""cli_correlator.py – CLI commands for CVE correlation."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from portwatch.correlator import correlate
from portwatch.snapshot import load_snapshot


def _default_snapshot_path() -> str:
    return "/var/lib/portwatch/snapshot.json"


def cmd_correlate(args: argparse.Namespace) -> None:
    """Cross-reference current snapshot against advisory database."""
    snapshot_path = Path(args.snapshot)
    ports = load_snapshot(snapshot_path)

    db_path = Path(args.db) if args.db else None
    report = correlate(list(ports.values()), db_path=db_path)

    if args.format == "json":
        print(json.dumps(report.as_dict(), indent=2))
    else:
        if not report.has_findings:
            print("No advisories matched open ports.")
        else:
            print(f"{'CVE ID':<20} {'SEV':<10} {'PORT':<8} {'SERVICE':<14} DESCRIPTION")
            print("-" * 80)
            for m in report.matches:
                print(
                    f"{m['cve_id']:<20} {m['severity']:<10} "
                    f"{m['port']:<8} {m['service']:<14} {m['description'][:50]}"
                )

    if report.has_findings:
        sys.exit(1)


def register_correlator_commands(
    subparsers: argparse._SubParsersAction,
) -> None:
    p = subparsers.add_parser(
        "correlate",
        help="Match open ports against CVE advisory database.",
    )
    p.add_argument(
        "--snapshot",
        default=_default_snapshot_path(),
        help="Path to snapshot JSON (default: %(default)s).",
    )
    p.add_argument(
        "--db",
        default=None,
        help="Path to advisory JSON database (uses bundled DB by default).",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    p.set_defaults(func=cmd_correlate)
