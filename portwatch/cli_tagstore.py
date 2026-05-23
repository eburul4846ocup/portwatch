"""CLI sub-commands for the tag store feature."""
from __future__ import annotations

import argparse
from pathlib import Path

from portwatch.tagstore import (
    add_tag,
    find_by_tag,
    get_tags,
    load_tags,
    remove_tag,
    save_tags,
)


def _default_tags_path() -> Path:
    return Path("/var/lib/portwatch/tags.json")


def cmd_tag_add(args: argparse.Namespace) -> int:
    path = Path(args.tags_file)
    tags = load_tags(path)
    tags = add_tag(tags, args.proto, args.port, args.tag)
    save_tags(path, tags)
    print(f"Tagged {args.proto}:{args.port} with '{args.tag}'")
    return 0


def cmd_tag_remove(args: argparse.Namespace) -> int:
    path = Path(args.tags_file)
    tags = load_tags(path)
    tags = remove_tag(tags, args.proto, args.port, args.tag)
    save_tags(path, tags)
    print(f"Removed tag '{args.tag}' from {args.proto}:{args.port}")
    return 0


def cmd_tag_list(args: argparse.Namespace) -> int:
    path = Path(args.tags_file)
    tags = load_tags(path)
    port_tags = get_tags(tags, args.proto, args.port)
    if port_tags:
        print(", ".join(port_tags))
    else:
        print(f"No tags for {args.proto}:{args.port}")
    return 0


def cmd_tag_find(args: argparse.Namespace) -> int:
    path = Path(args.tags_file)
    tags = load_tags(path)
    matches = find_by_tag(tags, args.tag)
    if not matches:
        print(f"No ports tagged '{args.tag}'")
        return 0
    for proto, port in sorted(matches):
        print(f"  {proto}:{port}")
    return 0


def register_tagstore_commands(sub: argparse._SubParsersAction, default_path: str) -> None:  # type: ignore[type-arg]
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--tags-file", default=default_path, metavar="PATH")

    p_add = sub.add_parser("tag-add", parents=[common], help="Add a tag to a port")
    p_add.add_argument("proto", choices=["tcp", "udp"])
    p_add.add_argument("port", type=int)
    p_add.add_argument("tag")
    p_add.set_defaults(func=cmd_tag_add)

    p_rm = sub.add_parser("tag-remove", parents=[common], help="Remove a tag from a port")
    p_rm.add_argument("proto", choices=["tcp", "udp"])
    p_rm.add_argument("port", type=int)
    p_rm.add_argument("tag")
    p_rm.set_defaults(func=cmd_tag_remove)

    p_ls = sub.add_parser("tag-list", parents=[common], help="List tags on a port")
    p_ls.add_argument("proto", choices=["tcp", "udp"])
    p_ls.add_argument("port", type=int)
    p_ls.set_defaults(func=cmd_tag_list)

    p_find = sub.add_parser("tag-find", parents=[common], help="Find ports by tag")
    p_find.add_argument("tag")
    p_find.set_defaults(func=cmd_tag_find)
