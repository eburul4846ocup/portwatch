"""CLI sub-commands for managing the custom service-name map."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from portwatch.svcmap import load_svcmap, lookup, remove_service, set_service

_DEFAULT_PATH = Path("~/.portwatch/svcmap.json")


def _svcmap_path(args: argparse.Namespace) -> Path:
    return Path(getattr(args, "svcmap_file", None) or _DEFAULT_PATH).expanduser()


def cmd_svc_set(args: argparse.Namespace) -> None:
    """Add or update a service name mapping."""
    path = _svcmap_path(args)
    set_service(path, args.proto, args.port, args.name)
    print(f"Mapped {args.proto.upper()}:{args.port} -> {args.name}")


def cmd_svc_remove(args: argparse.Namespace) -> None:
    """Remove a service name mapping."""
    path = _svcmap_path(args)
    removed = remove_service(path, args.proto, args.port)
    if removed:
        print(f"Removed mapping for {args.proto.upper()}:{args.port}")
    else:
        print(f"No mapping found for {args.proto.upper()}:{args.port}", file=sys.stderr)
        sys.exit(1)


def cmd_svc_list(args: argparse.Namespace) -> None:
    """List all custom service name mappings."""
    path = _svcmap_path(args)
    svcmap = load_svcmap(path)
    if not svcmap:
        print("No custom service mappings defined.")
        return
    print(f"{'Key':<20} {'Service Name'}")
    print("-" * 40)
    for key, name in sorted(svcmap.items()):
        print(f"{key:<20} {name}")


def cmd_svc_lookup(args: argparse.Namespace) -> None:
    """Look up the service name for a given proto/port."""
    path = _svcmap_path(args)
    custom = load_svcmap(path)
    name = lookup(args.proto, args.port, custom)
    if name:
        print(f"{args.proto.upper()}:{args.port} -> {name}")
    else:
        print(f"No service name found for {args.proto.upper()}:{args.port}")
        sys.exit(1)


def register_svcmap_commands(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--svcmap-file", dest="svcmap_file", default=None)

    p_set = sub.add_parser("svc-set", parents=[common], help="Add/update a service name")
    p_set.add_argument("proto", choices=["tcp", "udp"])
    p_set.add_argument("port", type=int)
    p_set.add_argument("name")
    p_set.set_defaults(func=cmd_svc_set)

    p_rm = sub.add_parser("svc-remove", parents=[common], help="Remove a service name")
    p_rm.add_argument("proto", choices=["tcp", "udp"])
    p_rm.add_argument("port", type=int)
    p_rm.set_defaults(func=cmd_svc_remove)

    p_list = sub.add_parser("svc-list", parents=[common], help="List all service names")
    p_list.set_defaults(func=cmd_svc_list)

    p_lookup = sub.add_parser("svc-lookup", parents=[common], help="Look up a service name")
    p_lookup.add_argument("proto", choices=["tcp", "udp"])
    p_lookup.add_argument("port", type=int)
    p_lookup.set_defaults(func=cmd_svc_lookup)
