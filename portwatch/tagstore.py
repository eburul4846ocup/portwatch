"""Tag store — attach user-defined labels/tags to ports and persist them."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

# Key: "<proto>:<port>"  Value: list of tag strings
TagMap = Dict[str, List[str]]


def _port_key(proto: str, port: int) -> str:
    return f"{proto}:{port}"


def load_tags(path: Path) -> TagMap:
    """Load tag map from *path*; return empty dict if file is absent or invalid."""
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
        if not isinstance(data, dict):
            return {}
        return {k: list(v) for k, v in data.items() if isinstance(v, list)}
    except (json.JSONDecodeError, OSError):
        return {}


def save_tags(path: Path, tags: TagMap) -> None:
    """Persist *tags* to *path*, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tags, indent=2))


def add_tag(tags: TagMap, proto: str, port: int, tag: str) -> TagMap:
    """Return a new TagMap with *tag* added to the entry for *proto*/*port*."""
    key = _port_key(proto, port)
    existing = list(tags.get(key, []))
    if tag not in existing:
        existing.append(tag)
    return {**tags, key: existing}


def remove_tag(tags: TagMap, proto: str, port: int, tag: str) -> TagMap:
    """Return a new TagMap with *tag* removed from *proto*/*port*."""
    key = _port_key(proto, port)
    existing = [t for t in tags.get(key, []) if t != tag]
    updated = dict(tags)
    if existing:
        updated[key] = existing
    else:
        updated.pop(key, None)
    return updated


def get_tags(tags: TagMap, proto: str, port: int) -> List[str]:
    """Return the list of tags for *proto*/*port* (may be empty)."""
    return list(tags.get(_port_key(proto, port), []))


def find_by_tag(tags: TagMap, tag: str) -> List[tuple[str, int]]:
    """Return all (proto, port) pairs that carry *tag*."""
    result = []
    for key, tag_list in tags.items():
        if tag in tag_list:
            proto, port_str = key.split(":", 1)
            result.append((proto, int(port_str)))
    return result
