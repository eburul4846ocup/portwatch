"""CLI sub-commands for service fingerprinting."""

from __future__ import annotations

import argparse
import json
import sys

from portwatch.fingerprint import fingerprint_ports
from portwatch.scanner import scan_ports


def cmd_fingerprint(args: argparse.Namespace) -> int:
    """Scan open ports and attempt to grab banners.

    Exits 0 on success, 1 on error.
    """
    host: str = args.host
    ports_arg: str | None = getattr(args, "ports", None)
    output_fmt: str = getattr(args, "format", "text")

    try:
        if ports_arg:
            port_numbers = [int(p.strip()) for p in ports_arg.split(",") if p.strip()]
            from portwatch.scanner import PortInfo

            open_ports = [PortInfo(port=p, proto="tcp", service="", state="open") for p in port_numbers]
        else:
            open_ports = scan_ports(host)
    except Exception as exc:  # noqa: BLE001
        print(f"[error] scan failed: {exc}", file=sys.stderr)
        return 1

    if not open_ports:
        print("No open ports found.")
        return 0

    fingerprints = fingerprint_ports(host, open_ports)

    if output_fmt == "json":
        data = [fp.as_dict() for fp in fingerprints.values()]
        print(json.dumps(data, indent=2))
    else:
        _print_text_table(fingerprints)

    return 0


def _print_text_table(fingerprints: dict) -> None:
    header = f"{'PORT':<8} {'VERSION HINT':<50} {'BANNER'}"
    print(header)
    print("-" * len(header))
    for port, fp in sorted(fingerprints.items()):
        version = fp.version_hint or "-"
        banner_preview = (fp.banner or "-")[:60]
        print(f"{port:<8} {version:<50} {banner_preview}")


def register_fingerprint_commands(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Attach the *fingerprint* sub-command to *subparsers*."""
    p = subparsers.add_parser(
        "fingerprint",
        help="Grab banners from open ports on a host.",
    )
    p.add_argument(
        "host",
        nargs="?",
        default="127.0.0.1",
        help="Target host (default: 127.0.0.1)",
    )
    p.add_argument(
        "--ports",
        metavar="PORT_LIST",
        help="Comma-separated list of ports to fingerprint instead of scanning.",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.set_defaults(func=cmd_fingerprint)
