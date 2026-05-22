"""CLI sub-commands for baseline management (approve / check)."""

from __future__ import annotations

import sys
import logging
from pathlib import Path

from portwatch.baseline import (
    approve_ports,
    load_baseline,
    read_baseline_comment,
    DEFAULT_BASELINE_PATH,
)
from portwatch.enforcer import enforce, BaselineMissingError
from portwatch.reporter import format_port_table, format_diff_report
from portwatch.scanner import scan_ports

logger = logging.getLogger(__name__)


def cmd_approve(args) -> int:
    """Scan current ports and save them as the new baseline."""
    path = Path(args.baseline)
    comment = getattr(args, "comment", "")
    ports = scan_ports()
    approve_ports(ports, path=path, comment=comment)
    print(f"Baseline approved ({len(ports)} ports saved to {path}).")
    if comment:
        print(f"Comment: {comment}")
    return 0


def cmd_show_baseline(args) -> int:
    """Display the currently approved baseline."""
    path = Path(args.baseline)
    ports = load_baseline(path)
    if ports is None:
        print(f"No baseline found at {path}.", file=sys.stderr)
        return 1
    comment = read_baseline_comment(path)
    if comment:
        print(f"Comment: {comment}")
    print(format_port_table(ports))
    return 0


def cmd_check(args) -> int:
    """Check whether the current host state matches the baseline."""
    path = Path(args.baseline)
    try:
        diff, compliant = enforce(baseline_path=path)
    except BaselineMissingError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if compliant:
        print("OK — host is compliant with baseline.")
        return 0

    print(format_diff_report(diff))
    return 1


def register_baseline_commands(subparsers) -> None:
    """Attach baseline sub-commands to an existing argparse subparsers object."""
    approve_p = subparsers.add_parser("approve", help="Approve current ports as baseline")
    approve_p.add_argument("--comment", default="", help="Optional approval comment")
    approve_p.set_defaults(func=cmd_approve)

    show_p = subparsers.add_parser("show-baseline", help="Display approved baseline")
    show_p.set_defaults(func=cmd_show_baseline)

    check_p = subparsers.add_parser("check", help="Verify host matches baseline")
    check_p.set_defaults(func=cmd_check)
