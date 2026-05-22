"""Command-line interface for portwatch."""

import argparse
import logging
import sys

from portwatch.daemon import run_daemon, run_once
from portwatch.config import load_config


def _setup_logging(verbose: bool):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        level=level,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="portwatch",
        description="Monitor open ports and alert on changes.",
    )
    parser.add_argument(
        "-c", "--config",
        default="portwatch.toml",
        metavar="FILE",
        help="Path to configuration file (default: portwatch.toml)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging",
    )

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("run", help="Start the background daemon loop")
    sub.add_parser(
        "scan",
        help="Perform a single scan and report changes without looping",
    )
    sub.add_parser(
        "show",
        help="Display the last saved snapshot",
    )
    return parser


def cmd_show(config_path: str):
    from portwatch.snapshot import load_snapshot
    config = load_config(config_path)
    ports = load_snapshot(config.snapshot_path)
    if not ports:
        print("No snapshot found.")
        return
    print(f"Snapshot for {config.host} ({len(ports)} open ports):")
    for p in sorted(ports, key=lambda x: x.port):
        print(f"  {p}")


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    _setup_logging(args.verbose)

    if args.command == "run":
        run_daemon(args.config)
    elif args.command == "scan":
        config = load_config(args.config)
        changed = run_once(config)
        sys.exit(0 if not changed else 1)
    elif args.command == "show":
        cmd_show(args.config)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
