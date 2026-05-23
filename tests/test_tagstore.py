"""Tests for portwatch.tagstore."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from portwatch.tagstore import (
    TagMap,
    add_tag,
    find_by_tag,
    get_tags,
    load_tags,
    remove_tag,
    save_tags,
)


@pytest.fixture()
def tags_file(tmp_path: Path) -> Path:
    return tmp_path / "tags.json"


def test_load_tags_missing_file(tags_file: Path) -> None:
    assert load_tags(tags_file) == {}


def test_load_tags_invalid_json(tags_file: Path) -> None:
    tags_file.write_text("not json")
    assert load_tags(tags_file) == {}


def test_save_and_load_roundtrip(tags_file: Path) -> None:
    tags: TagMap = {"tcp:22": ["ssh", "critical"]}
    save_tags(tags_file, tags)
    loaded = load_tags(tags_file)
    assert loaded == tags


def test_add_tag_new_port() -> None:
    tags = add_tag({}, "tcp", 22, "ssh")
    assert tags["tcp:22"] == ["ssh"]


def test_add_tag_existing_port() -> None:
    tags: TagMap = {"tcp:22": ["ssh"]}
    tags = add_tag(tags, "tcp", 22, "critical")
    assert "critical" in tags["tcp:22"]
    assert "ssh" in tags["tcp:22"]


def test_add_tag_no_duplicates() -> None:
    tags = add_tag({}, "tcp", 80, "web")
    tags = add_tag(tags, "tcp", 80, "web")
    assert tags["tcp:80"].count("web") == 1


def test_remove_tag_existing() -> None:
    tags: TagMap = {"tcp:22": ["ssh", "critical"]}
    tags = remove_tag(tags, "tcp", 22, "critical")
    assert tags["tcp:22"] == ["ssh"]


def test_remove_tag_last_removes_key() -> None:
    tags: TagMap = {"tcp:22": ["ssh"]}
    tags = remove_tag(tags, "tcp", 22, "ssh")
    assert "tcp:22" not in tags


def test_remove_tag_absent_is_noop() -> None:
    tags: TagMap = {"tcp:22": ["ssh"]}
    result = remove_tag(tags, "tcp", 22, "nonexistent")
    assert result == tags


def test_get_tags_present() -> None:
    tags: TagMap = {"tcp:443": ["https", "public"]}
    assert get_tags(tags, "tcp", 443) == ["https", "public"]


def test_get_tags_absent() -> None:
    assert get_tags({}, "tcp", 9999) == []


def test_find_by_tag_single() -> None:
    tags: TagMap = {"tcp:22": ["ssh"], "tcp:80": ["web"]}
    result = find_by_tag(tags, "ssh")
    assert result == [("tcp", 22)]


def test_find_by_tag_multiple() -> None:
    tags: TagMap = {"tcp:22": ["critical"], "tcp:443": ["critical", "https"]}
    result = find_by_tag(tags, "critical")
    assert set(result) == {("tcp", 22), ("tcp", 443)}


def test_find_by_tag_no_match() -> None:
    assert find_by_tag({"tcp:22": ["ssh"]}, "missing") == []
