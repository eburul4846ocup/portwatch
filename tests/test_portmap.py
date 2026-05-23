"""Tests for portwatch.portmap."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from portwatch.portmap import (
    load_portmap,
    save_portmap,
    set_description,
    remove_description,
    lookup,
    _port_key,
)


@pytest.fixture()
def portmap_file(tmp_path: Path) -> Path:
    return tmp_path / "portmap.json"


def test_port_key_format():
    assert _port_key(80, "tcp") == "80/tcp"
    assert _port_key(443, "TCP") == "443/tcp"  # normalised to lower


def test_load_portmap_missing_file(portmap_file: Path):
    result = load_portmap(portmap_file)
    assert result == {}


def test_load_portmap_invalid_json(portmap_file: Path):
    portmap_file.write_text("not-json")
    result = load_portmap(portmap_file)
    assert result == {}


def test_load_portmap_wrong_type(portmap_file: Path):
    portmap_file.write_text(json.dumps(["a", "b"]))
    result = load_portmap(portmap_file)
    assert result == {}


def test_save_and_load_roundtrip(portmap_file: Path):
    data = {"22/tcp": "SSH", "80/tcp": "HTTP"}
    save_portmap(portmap_file, data)
    loaded = load_portmap(portmap_file)
    assert loaded == data


def test_set_description_creates_entry(portmap_file: Path):
    set_description(portmap_file, 8080, "tcp", "Dev HTTP")
    data = load_portmap(portmap_file)
    assert data["8080/tcp"] == "Dev HTTP"


def test_set_description_overwrites_existing(portmap_file: Path):
    set_description(portmap_file, 22, "tcp", "SSH")
    set_description(portmap_file, 22, "tcp", "OpenSSH override")
    data = load_portmap(portmap_file)
    assert data["22/tcp"] == "OpenSSH override"


def test_remove_description_existing(portmap_file: Path):
    set_description(portmap_file, 443, "tcp", "HTTPS")
    removed = remove_description(portmap_file, 443, "tcp")
    assert removed is True
    assert load_portmap(portmap_file) == {}


def test_remove_description_missing(portmap_file: Path):
    removed = remove_description(portmap_file, 9999, "tcp")
    assert removed is False


def test_lookup_returns_description(portmap_file: Path):
    set_description(portmap_file, 22, "tcp", "SSH")
    data = load_portmap(portmap_file)
    assert lookup(data, 22, "tcp") == "SSH"


def test_lookup_returns_none_for_unknown(portmap_file: Path):
    data = load_portmap(portmap_file)
    assert lookup(data, 12345, "tcp") is None


def test_save_creates_parent_dirs(tmp_path: Path):
    nested = tmp_path / "a" / "b" / "portmap.json"
    save_portmap(nested, {"22/tcp": "SSH"})
    assert nested.exists()
