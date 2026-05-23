"""Tests for portwatch.cli_tagstore CLI commands."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from portwatch.cli_tagstore import (
    cmd_tag_add,
    cmd_tag_find,
    cmd_tag_list,
    cmd_tag_remove,
    register_tagstore_commands,
)
from portwatch.tagstore import load_tags, save_tags


def _ns(tags_file: str, **kwargs: object) -> argparse.Namespace:
    return argparse.Namespace(tags_file=tags_file, **kwargs)


def test_cmd_tag_add_creates_entry(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    f = str(tmp_path / "tags.json")
    rc = cmd_tag_add(_ns(f, proto="tcp", port=22, tag="ssh"))
    assert rc == 0
    tags = load_tags(Path(f))
    assert "ssh" in tags.get("tcp:22", [])
    out = capsys.readouterr().out
    assert "ssh" in out


def test_cmd_tag_remove_removes_entry(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    f = tmp_path / "tags.json"
    save_tags(f, {"tcp:22": ["ssh", "critical"]})
    rc = cmd_tag_remove(_ns(str(f), proto="tcp", port=22, tag="critical"))
    assert rc == 0
    tags = load_tags(f)
    assert "critical" not in tags.get("tcp:22", [])


def test_cmd_tag_list_shows_tags(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    f = tmp_path / "tags.json"
    save_tags(f, {"tcp:443": ["https", "public"]})
    rc = cmd_tag_list(_ns(str(f), proto="tcp", port=443))
    assert rc == 0
    out = capsys.readouterr().out
    assert "https" in out
    assert "public" in out


def test_cmd_tag_list_no_tags(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    f = tmp_path / "tags.json"
    rc = cmd_tag_list(_ns(str(f), proto="tcp", port=9999))
    assert rc == 0
    out = capsys.readouterr().out
    assert "No tags" in out


def test_cmd_tag_find_returns_ports(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    f = tmp_path / "tags.json"
    save_tags(f, {"tcp:22": ["critical"], "tcp:443": ["critical"]})
    rc = cmd_tag_find(_ns(str(f), tag="critical"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "tcp:22" in out
    assert "tcp:443" in out


def test_cmd_tag_find_no_match(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    f = tmp_path / "tags.json"
    rc = cmd_tag_find(_ns(str(f), tag="ghost"))
    assert rc == 0
    assert "No ports" in capsys.readouterr().out


def test_register_tagstore_commands_registers_subparsers() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_tagstore_commands(sub, "/tmp/tags.json")
    args = parser.parse_args(["tag-add", "tcp", "22", "ssh"])
    assert args.port == 22
    assert args.tag == "ssh"
