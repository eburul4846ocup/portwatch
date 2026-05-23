"""CLI commands for managing CIDR exclusion filters."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from portwatch.cidr_filter import CIDRFilter, load_cidr_filter, save_cidr_filter


def _default_filter_path() -> Path:
    return Path("portwatch_cidr.json")


def cmd_cidr_add(args: argparse.Namespace) -> None:
    """Add a CIDR range to the exclusion list."""
    path = Path(args.file)
    cf = load_cidr_filter(path)
    if args.cidr in cf.excluded:
        print(f"[cidr] {args.cidr} is already in the exclusion list.")
        return
    cf.excluded.append(args.cidr)
    # Validate by reconstructing
    updated = CIDRFilter(excluded=cf.excluded)
    if args.cidr not in [str(e) for e in cf.excluded]:
        print(f"[cidr] Warning: {args.cidr} may be invalid.", file=sys.stderr)
    save_cidr_filter(path, updated)
    print(f"[cidr] Added {args.cidr}")


def cmd_cidr_remove(args: argparse.Namespace) -> None:
    """Remove a CIDR range from the exclusion list."""
    path = Path(args.file)
    cf = load_cidr_filter(path)
    if args.cidr not in cf.excluded:
        print(f"[cidr] {args.cidr} not found in exclusion list.", file=sys.stderr)
        sys.exit(1)
    cf.excluded.remove(args.cidr)
    save_cidr_filter(path, CIDRFilter(excluded=cf.excluded))
    print(f"[cidr] Removed {args.cidr}")


def cmd_cidr_list(args: argparse.Namespace) -> None:
    """List all excluded CIDR ranges."""
    path = Path(args.file)
    cf = load_cidr_filter(path)
    if not cf.excluded:
        print("[cidr] No exclusions configured.")
        return
    print("Excluded CIDR ranges:")
    for entry in cf.excluded:
        print(f"  {entry}")


def cmd_cidr_check(args: argparse.Namespace) -> None:
    """Check whether a given IP address is excluded."""
    path = Path(args.file)
    cf = load_cidr_filter(path)
    if cf.is_excluded(args.address):
        print(f"[cidr] {args.address} is EXCLUDED")
        sys.exit(1)
    else:
        print(f"[cidr] {args.address} is NOT excluded")


def register_cidr_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--file", default=str(_default_filter_path()), help="Path to CIDR filter JSON"
    )

    p_add = subparsers.add_parser("cidr-add", parents=[common], help="Add a CIDR exclusion")
    p_add.add_argument("cidr", help="CIDR range, e.g. 10.0.0.0/8")
    p_add.set_defaults(func=cmd_cidr_add)

    p_rm = subparsers.add_parser("cidr-remove", parents=[common], help="Remove a CIDR exclusion")
    p_rm.add_argument("cidr", help="CIDR range to remove")
    p_rm.set_defaults(func=cmd_cidr_remove)

    p_ls = subparsers.add_parser("cidr-list", parents=[common], help="List CIDR exclusions")
    p_ls.set_defaults(func=cmd_cidr_list)

    p_chk = subparsers.add_parser("cidr-check", parents=[common], help="Check if an IP is excluded")
    p_chk.add_argument("address", help="IP address to test")
    p_chk.set_defaults(func=cmd_cidr_check)
