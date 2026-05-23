"""CLI sub-commands for managing host labels."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from portwatch.hostlabel import (
    get_label,
    list_labels,
    remove_label,
    set_label,
)


def _default_labels_path() -> Path:
    return Path("/var/lib/portwatch/hostlabels.json")


def cmd_label_set(args: argparse.Namespace) -> None:
    path = Path(args.labels_file)
    set_label(path, args.ip, args.label, role=args.role)
    print(f"Label set: {args.ip} → {args.label}" + (f" [{args.role}]" if args.role else ""))


def cmd_label_remove(args: argparse.Namespace) -> None:
    path = Path(args.labels_file)
    if remove_label(path, args.ip):
        print(f"Removed label for {args.ip}")
    else:
        print(f"No label found for {args.ip}", file=sys.stderr)
        sys.exit(1)


def cmd_label_list(args: argparse.Namespace) -> None:
    path = Path(args.labels_file)
    rows = list_labels(path)
    if not rows:
        print("(no host labels defined)")
        return
    print(f"{'IP':<20} {'LABEL':<24} ROLE")
    print("-" * 56)
    for ip, label, role in rows:
        print(f"{ip:<20} {label:<24} {role or '-'}")


def cmd_label_lookup(args: argparse.Namespace) -> None:
    path = Path(args.labels_file)
    entry = get_label(path, args.ip)
    if entry is None:
        print(f"No label found for {args.ip}", file=sys.stderr)
        sys.exit(1)
    print(f"{args.ip}: {entry['label']}" + (f" [{entry['role']}]" if entry.get("role") else ""))


def register_hostlabel_commands(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    default_path = str(_default_labels_path())
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--labels-file", default=default_path, metavar="FILE")

    p_set = sub.add_parser("label-set", parents=[common], help="Assign a label to an IP")
    p_set.add_argument("ip")
    p_set.add_argument("label")
    p_set.add_argument("--role", default=None, help="Optional role tag (e.g. web, db)")
    p_set.set_defaults(func=cmd_label_set)

    p_rm = sub.add_parser("label-remove", parents=[common], help="Remove label for an IP")
    p_rm.add_argument("ip")
    p_rm.set_defaults(func=cmd_label_remove)

    p_ls = sub.add_parser("label-list", parents=[common], help="List all host labels")
    p_ls.set_defaults(func=cmd_label_list)

    p_lk = sub.add_parser("label-lookup", parents=[common], help="Look up label for an IP")
    p_lk.add_argument("ip")
    p_lk.set_defaults(func=cmd_label_lookup)
