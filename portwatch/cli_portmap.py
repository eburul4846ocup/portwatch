"""cli_portmap.py — CLI sub-commands for managing the port description map."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from portwatch.portmap import (
    load_portmap,
    set_description,
    remove_description,
    lookup,
)

_DEFAULT_PORTMAP = Path("portwatch_portmap.json")


def _portmap_path(args: argparse.Namespace) -> Path:
    return Path(getattr(args, "portmap_file", None) or _DEFAULT_PORTMAP)


def cmd_pm_set(args: argparse.Namespace) -> None:
    """Set a custom description for a port."""
    path = _portmap_path(args)
    set_description(path, args.port, args.proto, args.description)
    print(f"Saved: {args.port}/{args.proto} → {args.description!r}")


def cmd_pm_remove(args: argparse.Namespace) -> None:
    """Remove a custom description for a port."""
    path = _portmap_path(args)
    removed = remove_description(path, args.port, args.proto)
    if removed:
        print(f"Removed description for {args.port}/{args.proto}.")
    else:
        print(f"No description found for {args.port}/{args.proto}.")
        sys.exit(1)


def cmd_pm_list(args: argparse.Namespace) -> None:
    """List all custom port descriptions."""
    path = _portmap_path(args)
    data = load_portmap(path)
    if not data:
        print("No custom port descriptions defined.")
        return
    width = max(len(k) for k in data)
    print(f"{'PORT/PROTO':<{width}}  DESCRIPTION")
    print("-" * (width + 14))
    for key in sorted(data):
        print(f"{key:<{width}}  {data[key]}")


def cmd_pm_lookup(args: argparse.Namespace) -> None:
    """Look up the description for a specific port."""
    path = _portmap_path(args)
    data = load_portmap(path)
    desc = lookup(data, args.port, args.proto)
    if desc is None:
        print(f"No custom description for {args.port}/{args.proto}.")
        sys.exit(1)
    print(desc)


def register_portmap_commands(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--portmap-file", metavar="PATH", help="Path to portmap JSON file")

    p_set = sub.add_parser("pm-set", parents=[common], help="Set a port description")
    p_set.add_argument("port", type=int)
    p_set.add_argument("proto", choices=["tcp", "udp"])
    p_set.add_argument("description")
    p_set.set_defaults(func=cmd_pm_set)

    p_rm = sub.add_parser("pm-remove", parents=[common], help="Remove a port description")
    p_rm.add_argument("port", type=int)
    p_rm.add_argument("proto", choices=["tcp", "udp"])
    p_rm.set_defaults(func=cmd_pm_remove)

    p_list = sub.add_parser("pm-list", parents=[common], help="List all port descriptions")
    p_list.set_defaults(func=cmd_pm_list)

    p_look = sub.add_parser("pm-lookup", parents=[common], help="Look up a port description")
    p_look.add_argument("port", type=int)
    p_look.add_argument("proto", choices=["tcp", "udp"])
    p_look.set_defaults(func=cmd_pm_lookup)
