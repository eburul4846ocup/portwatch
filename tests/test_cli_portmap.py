"""Tests for portwatch.cli_portmap CLI commands."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from portwatch.cli_portmap import (
    cmd_pm_set,
    cmd_pm_remove,
    cmd_pm_list,
    cmd_pm_lookup,
)
from portwatch.portmap import load_portmap, set_description


def _ns(portmap_file: Path, **kwargs) -> argparse.Namespace:
    return argparse.Namespace(portmap_file=str(portmap_file), **kwargs)


def test_cmd_pm_set_creates_entry(tmp_path: Path, capsys):
    f = tmp_path / "pm.json"
    cmd_pm_set(_ns(f, port=8080, proto="tcp", description="Dev server"))
    data = load_portmap(f)
    assert data["8080/tcp"] == "Dev server"
    out = capsys.readouterr().out
    assert "8080/tcp" in out
    assert "Dev server" in out


def test_cmd_pm_remove_existing_entry(tmp_path: Path, capsys):
    f = tmp_path / "pm.json"
    set_description(f, 22, "tcp", "SSH")
    cmd_pm_remove(_ns(f, port=22, proto="tcp"))
    assert load_portmap(f) == {}
    out = capsys.readouterr().out
    assert "Removed" in out


def test_cmd_pm_remove_missing_entry_exits_one(tmp_path: Path):
    f = tmp_path / "pm.json"
    with pytest.raises(SystemExit) as exc_info:
        cmd_pm_remove(_ns(f, port=9999, proto="tcp"))
    assert exc_info.value.code == 1


def test_cmd_pm_list_empty(tmp_path: Path, capsys):
    f = tmp_path / "pm.json"
    cmd_pm_list(_ns(f))
    out = capsys.readouterr().out
    assert "No custom" in out


def test_cmd_pm_list_shows_entries(tmp_path: Path, capsys):
    f = tmp_path / "pm.json"
    set_description(f, 22, "tcp", "SSH")
    set_description(f, 80, "tcp", "HTTP")
    cmd_pm_list(_ns(f))
    out = capsys.readouterr().out
    assert "22/tcp" in out
    assert "SSH" in out
    assert "80/tcp" in out
    assert "HTTP" in out


def test_cmd_pm_lookup_found(tmp_path: Path, capsys):
    f = tmp_path / "pm.json"
    set_description(f, 443, "tcp", "HTTPS")
    cmd_pm_lookup(_ns(f, port=443, proto="tcp"))
    out = capsys.readouterr().out
    assert "HTTPS" in out


def test_cmd_pm_lookup_not_found_exits_one(tmp_path: Path):
    f = tmp_path / "pm.json"
    with pytest.raises(SystemExit) as exc_info:
        cmd_pm_lookup(_ns(f, port=12345, proto="tcp"))
    assert exc_info.value.code == 1
