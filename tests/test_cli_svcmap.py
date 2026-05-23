"""Unit tests for portwatch.cli_svcmap command handlers."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from portwatch.cli_svcmap import (
    cmd_svc_list,
    cmd_svc_lookup,
    cmd_svc_remove,
    cmd_svc_set,
)
from portwatch.svcmap import load_svcmap, set_service


def _ns(tmp_path: Path, **kwargs) -> argparse.Namespace:  # type: ignore[type-arg]
    defaults = {"svcmap_file": str(tmp_path / "svcmap.json"), "proto": "tcp", "port": 80}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_svc_set_creates_entry(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    args = _ns(tmp_path, port=9200, name="Elasticsearch")
    cmd_svc_set(args)
    out = capsys.readouterr().out
    assert "Elasticsearch" in out
    svcmap = load_svcmap(Path(args.svcmap_file))
    assert svcmap.get("tcp:9200") == "Elasticsearch"


def test_cmd_svc_remove_existing(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    path = tmp_path / "svcmap.json"
    set_service(path, "tcp", 3000, "DevServer")
    args = _ns(tmp_path, svcmap_file=str(path), port=3000)
    cmd_svc_remove(args)
    out = capsys.readouterr().out
    assert "Removed" in out
    assert "tcp:3000" not in load_svcmap(path)


def test_cmd_svc_remove_missing_exits_one(tmp_path: Path) -> None:
    args = _ns(tmp_path, port=9999)
    with pytest.raises(SystemExit) as exc_info:
        cmd_svc_remove(args)
    assert exc_info.value.code == 1


def test_cmd_svc_list_empty(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    args = _ns(tmp_path)
    cmd_svc_list(args)
    out = capsys.readouterr().out
    assert "No custom" in out


def test_cmd_svc_list_shows_entries(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    path = tmp_path / "svcmap.json"
    set_service(path, "tcp", 8080, "MyApp")
    args = _ns(tmp_path, svcmap_file=str(path))
    cmd_svc_list(args)
    out = capsys.readouterr().out
    assert "tcp:8080" in out
    assert "MyApp" in out


def test_cmd_svc_lookup_found(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    args = _ns(tmp_path, port=22)  # built-in SSH
    cmd_svc_lookup(args)
    out = capsys.readouterr().out
    assert "SSH" in out


def test_cmd_svc_lookup_not_found_exits_one(tmp_path: Path) -> None:
    args = _ns(tmp_path, port=19999)
    with pytest.raises(SystemExit) as exc_info:
        cmd_svc_lookup(args)
    assert exc_info.value.code == 1
