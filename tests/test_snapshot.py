"""Tests for the snapshot persistence and diffing logic."""

import json
import pytest
from pathlib import Path

from portwatch.scanner import PortInfo
from portwatch.snapshot import save_snapshot, load_snapshot, diff_snapshots


@pytest.fixture
def sample_ports() -> list[PortInfo]:
    return [
        PortInfo(port=22, protocol="tcp", service="ssh"),
        PortInfo(port=80, protocol="tcp", service="http"),
        PortInfo(port=443, protocol="tcp", service="https"),
    ]


def test_save_and_load_snapshot(tmp_path: Path, sample_ports: list[PortInfo]) -> None:
    snapshot_file = tmp_path / "snapshot.json"
    save_snapshot(sample_ports, path=snapshot_file)

    assert snapshot_file.exists()
    loaded = load_snapshot(path=snapshot_file)
    assert loaded is not None
    assert len(loaded) == len(sample_ports)
    assert loaded[0].port == 22
    assert loaded[0].protocol == "tcp"
    assert loaded[0].service == "ssh"


def test_load_snapshot_missing_file(tmp_path: Path) -> None:
    result = load_snapshot(path=tmp_path / "nonexistent.json")
    assert result is None


def test_load_snapshot_invalid_json(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("not valid json{{{")
    result = load_snapshot(path=bad_file)
    assert result is None


def test_diff_no_changes(sample_ports: list[PortInfo]) -> None:
    diff = diff_snapshots(sample_ports, sample_ports)
    assert diff["appeared"] == []
    assert diff["disappeared"] == []


def test_diff_new_port_appeared(sample_ports: list[PortInfo]) -> None:
    new_port = PortInfo(port=8080, protocol="tcp", service="http-alt")
    current = sample_ports + [new_port]
    diff = diff_snapshots(sample_ports, current)
    assert len(diff["appeared"]) == 1
    assert diff["appeared"][0].port == 8080
    assert diff["disappeared"] == []


def test_diff_port_disappeared(sample_ports: list[PortInfo]) -> None:
    current = [p for p in sample_ports if p.port != 80]
    diff = diff_snapshots(sample_ports, current)
    assert diff["appeared"] == []
    assert len(diff["disappeared"]) == 1
    assert diff["disappeared"][0].port == 80


def test_diff_simultaneous_changes(sample_ports: list[PortInfo]) -> None:
    new_port = PortInfo(port=3306, protocol="tcp", service="mysql")
    current = [p for p in sample_ports if p.port != 443] + [new_port]
    diff = diff_snapshots(sample_ports, current)
    appeared_ports = {p.port for p in diff["appeared"]}
    disappeared_ports = {p.port for p in diff["disappeared"]}
    assert appeared_ports == {3306}
    assert disappeared_ports == {443}
