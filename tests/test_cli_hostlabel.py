"""Tests for portwatch.cli_hostlabel sub-commands."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from portwatch.cli_hostlabel import (
    cmd_label_list,
    cmd_label_lookup,
    cmd_label_remove,
    cmd_label_set,
)


def _ns(tmp_path: Path, **kwargs) -> argparse.Namespace:  # type: ignore[type-arg]
    defaults = {"labels_file": str(tmp_path / "labels.json")}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_label_set_creates_entry(tmp_path: Path, capsys) -> None:
    ns = _ns(tmp_path, ip="10.0.0.1", label="webserver", role="web")
    cmd_label_set(ns)
    captured = capsys.readouterr()
    assert "10.0.0.1" in captured.out
    assert "webserver" in captured.out
    assert "web" in captured.out


def test_cmd_label_set_no_role(tmp_path: Path, capsys) -> None:
    ns = _ns(tmp_path, ip="10.0.0.2", label="db", role=None)
    cmd_label_set(ns)
    captured = capsys.readouterr()
    assert "db" in captured.out


def test_cmd_label_remove_existing(tmp_path: Path, capsys) -> None:
    ns_set = _ns(tmp_path, ip="10.0.0.3", label="temp", role=None)
    cmd_label_set(ns_set)
    ns_rm = _ns(tmp_path, ip="10.0.0.3")
    cmd_label_remove(ns_rm)
    captured = capsys.readouterr()
    assert "Removed" in captured.out


def test_cmd_label_remove_missing_exits_one(tmp_path: Path) -> None:
    ns = _ns(tmp_path, ip="9.9.9.9")
    with pytest.raises(SystemExit) as exc:
        cmd_label_remove(ns)
    assert exc.value.code == 1


def test_cmd_label_list_shows_entries(tmp_path: Path, capsys) -> None:
    for ip, label, role in [("10.0.0.1", "web", "web"), ("10.0.0.2", "db", None)]:
        cmd_label_set(_ns(tmp_path, ip=ip, label=label, role=role))
    capsys.readouterr()
    cmd_label_list(_ns(tmp_path))
    out = capsys.readouterr().out
    assert "10.0.0.1" in out
    assert "10.0.0.2" in out
    assert "web" in out


def test_cmd_label_list_empty(tmp_path: Path, capsys) -> None:
    cmd_label_list(_ns(tmp_path))
    out = capsys.readouterr().out
    assert "no host labels" in out


def test_cmd_label_lookup_found(tmp_path: Path, capsys) -> None:
    cmd_label_set(_ns(tmp_path, ip="1.2.3.4", label="router", role="network"))
    capsys.readouterr()
    cmd_label_lookup(_ns(tmp_path, ip="1.2.3.4"))
    out = capsys.readouterr().out
    assert "router" in out


def test_cmd_label_lookup_missing_exits_one(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exc:
        cmd_label_lookup(_ns(tmp_path, ip="0.0.0.0"))
    assert exc.value.code == 1
