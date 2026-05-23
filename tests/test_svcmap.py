"""Unit tests for portwatch.svcmap."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from portwatch.svcmap import (
    _BUILTIN,
    _port_key,
    load_svcmap,
    lookup,
    remove_service,
    save_svcmap,
    set_service,
)


@pytest.fixture()
def svcmap_file(tmp_path: Path) -> Path:
    return tmp_path / "svcmap.json"


def test_port_key_format() -> None:
    assert _port_key("TCP", 443) == "tcp:443"
    assert _port_key("udp", 53) == "udp:53"


def test_load_svcmap_missing_file(svcmap_file: Path) -> None:
    result = load_svcmap(svcmap_file)
    assert result == {}


def test_load_svcmap_invalid_json(svcmap_file: Path) -> None:
    svcmap_file.write_text("not json")
    result = load_svcmap(svcmap_file)
    assert result == {}


def test_load_svcmap_wrong_type(svcmap_file: Path) -> None:
    svcmap_file.write_text(json.dumps(["tcp:80", "HTTP"]))
    result = load_svcmap(svcmap_file)
    assert result == {}


def test_save_and_load_roundtrip(svcmap_file: Path) -> None:
    data = {"tcp:8080": "MyApp", "tcp:9090": "Metrics"}
    save_svcmap(svcmap_file, data)
    loaded = load_svcmap(svcmap_file)
    assert loaded == data


def test_set_service_creates_entry(svcmap_file: Path) -> None:
    result = set_service(svcmap_file, "tcp", 9200, "Elasticsearch")
    assert result["tcp:9200"] == "Elasticsearch"
    assert load_svcmap(svcmap_file)["tcp:9200"] == "Elasticsearch"


def test_set_service_overwrites_existing(svcmap_file: Path) -> None:
    set_service(svcmap_file, "tcp", 80, "HTTP")
    set_service(svcmap_file, "tcp", 80, "Nginx")
    assert load_svcmap(svcmap_file)["tcp:80"] == "Nginx"


def test_remove_service_existing(svcmap_file: Path) -> None:
    set_service(svcmap_file, "tcp", 3000, "DevServer")
    removed = remove_service(svcmap_file, "tcp", 3000)
    assert removed is True
    assert "tcp:3000" not in load_svcmap(svcmap_file)


def test_remove_service_missing(svcmap_file: Path) -> None:
    removed = remove_service(svcmap_file, "tcp", 9999)
    assert removed is False


def test_lookup_builtin() -> None:
    assert lookup("tcp", 22) == "SSH"
    assert lookup("tcp", 443) == "HTTPS"


def test_lookup_custom_overrides_builtin(svcmap_file: Path) -> None:
    custom = load_svcmap(svcmap_file)
    custom["tcp:22"] = "SecureShell"
    result = lookup("tcp", 22, custom)
    assert result == "SecureShell"


def test_lookup_unknown_port_returns_none() -> None:
    assert lookup("tcp", 19999) is None


def test_builtin_map_non_empty() -> None:
    assert len(_BUILTIN) > 0
    assert "tcp:80" in _BUILTIN
