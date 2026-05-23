"""CLI sub-commands for managing the port watchlist."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from portwatch.scanner import scan_ports
from portwatch.watchlist import (
    WatchlistEntry,
    check_watchlist,
    load_watchlist,
    save_watchlist,
)

_DEFAULT_WATCHLIST = Path("/etc/portwatch/watchlist.json")


def _watchlist_path(args: argparse.Namespace) -> Path:
    return Path(getattr(args, "watchlist", None) or _DEFAULT_WATCHLIST)


def cmd_wl_add(args: argparse.Namespace) -> int:
    path = _watchlist_path(args)
    entries = load_watchlist(path)
    required = not args.forbidden
    entry = WatchlistEntry(
        port=args.port,
        protocol=args.protocol,
        required=required,
        label=args.label,
    )
    entries.append(entry)
    save_watchlist(path, entries)
    kind = "required" if required else "forbidden"
    print(f"Added {kind} watchlist entry: {args.port}/{args.protocol}")
    return 0


def cmd_wl_list(args: argparse.Namespace) -> int:
    path = _watchlist_path(args)
    entries = load_watchlist(path)
    if not entries:
        print("Watchlist is empty.")
        return 0
    for e in entries:
        kind = "REQUIRED" if e.required else "FORBIDDEN"
        label = f"  ({e.label})" if e.label else ""
        print(f"  [{kind}] {e.port}/{e.protocol}{label}")
    return 0


def cmd_wl_check(args: argparse.Namespace) -> int:
    path = _watchlist_path(args)
    entries = load_watchlist(path)
    if not entries:
        print("Watchlist is empty — nothing to check.")
        return 0
    open_ports = scan_ports()
    violations = check_watchlist(entries, open_ports)
    if not violations:
        print("All watchlist checks passed.")
        return 0
    print(f"{len(violations)} watchlist violation(s):")
    for v in violations:
        print(f"  {v.message}")
    return 1


def register_watchlist_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    wl = subparsers.add_parser("watchlist", help="Manage port watchlist")
    ws = wl.add_subparsers(dest="wl_cmd")

    add_p = ws.add_parser("add", help="Add a watchlist entry")
    add_p.add_argument("port", type=int)
    add_p.add_argument("--protocol", default="tcp")
    add_p.add_argument("--forbidden", action="store_true", help="Port must be closed")
    add_p.add_argument("--label", default=None)
    add_p.set_defaults(func=cmd_wl_add)

    ls_p = ws.add_parser("list", help="List watchlist entries")
    ls_p.set_defaults(func=cmd_wl_list)

    chk_p = ws.add_parser("check", help="Check watchlist against live ports")
    chk_p.set_defaults(func=cmd_wl_check)
