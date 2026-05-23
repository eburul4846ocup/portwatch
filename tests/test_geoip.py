"""Tests for portwatch.geoip."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from portwatch.geoip import GeoInfo, lookup, resolve_hostname, _load_cache, _save_cache


@pytest.fixture()
def cache_file(tmp_path: Path) -> Path:
    return tmp_path / "geoip_cache.json"


# ---------------------------------------------------------------------------
# GeoInfo
# ---------------------------------------------------------------------------

def test_geoinfo_as_dict():
    info = GeoInfo(ip="1.2.3.4", country="DE", city="Berlin", asn="AS1234")
    d = info.as_dict()
    assert d == {"ip": "1.2.3.4", "country": "DE", "city": "Berlin", "asn": "AS1234"}


def test_geoinfo_defaults():
    info = GeoInfo(ip="10.0.0.1")
    assert info.country == "unknown"
    assert info.city == "unknown"
    assert info.asn == "unknown"


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def test_save_and_load_cache(cache_file: Path):
    data = {"1.1.1.1": {"country": "AU", "city": "Sydney", "asn": "AS13335"}}
    _save_cache(cache_file, data)
    loaded = _load_cache(cache_file)
    assert loaded == data


def test_load_cache_missing_file(tmp_path: Path):
    result = _load_cache(tmp_path / "nonexistent.json")
    assert result == {}


def test_load_cache_invalid_json(cache_file: Path):
    cache_file.write_text("not json")
    result = _load_cache(cache_file)
    assert result == {}


# ---------------------------------------------------------------------------
# resolve_hostname
# ---------------------------------------------------------------------------

def test_resolve_hostname_returns_ip_on_failure():
    with patch("portwatch.geoip.socket.gethostbyaddr", side_effect=OSError):
        result = resolve_hostname("192.0.2.1")
    assert result == "192.0.2.1"


def test_resolve_hostname_success():
    with patch(
        "portwatch.geoip.socket.gethostbyaddr",
        return_value=("example.com", [], ["93.184.216.34"]),
    ):
        result = resolve_hostname("93.184.216.34")
    assert result == "example.com"


# ---------------------------------------------------------------------------
# lookup
# ---------------------------------------------------------------------------

def test_lookup_uses_cache_on_hit(cache_file: Path):
    cached = {"1.2.3.4": {"ip": "1.2.3.4", "country": "US", "city": "NYC", "asn": "AS1"}}
    cache_file.write_text(json.dumps(cached))
    info = lookup("1.2.3.4", cache_path=cache_file)
    assert info.country == "US"
    assert info.city == "NYC"


def test_lookup_writes_to_cache(cache_file: Path):
    with patch("portwatch.geoip.socket.gethostbyaddr", side_effect=OSError):
        info = lookup("5.6.7.8", cache_path=cache_file)
    assert cache_file.exists()
    data = json.loads(cache_file.read_text())
    assert "5.6.7.8" in data


def test_lookup_without_cache_does_not_create_file(tmp_path: Path):
    with patch("portwatch.geoip.socket.gethostbyaddr", side_effect=OSError):
        info = lookup("9.9.9.9", cache_path=None)
    assert info.ip == "9.9.9.9"


def test_lookup_extracts_country_from_hostname(cache_file: Path):
    with patch(
        "portwatch.geoip.socket.gethostbyaddr",
        return_value=("host.example.de", [], ["1.2.3.4"]),
    ):
        info = lookup("1.2.3.4", cache_path=cache_file)
    assert info.country == "DE"
