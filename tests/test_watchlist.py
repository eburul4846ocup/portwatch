"""Tests for portwatch.watchlist."""
import json
import pytest
from pathlib import Path

from portwatch.scanner import PortInfo
from portwatch.watchlist import (
    WatchlistEntry,
    WatchlistViolation,
    check_watchlist,
    load_watchlist,
    save_watchlist,
)


@pytest.fixture
def ssh_port():
    return PortInfo(port=22, protocol="tcp", state="open", service="ssh")


@pytest.fixture
def http_port():
    return PortInfo(port=80, protocol="tcp", state="open", service="http")


@pytest.fixture
def watchlist_file(tmp_path):
    return tmp_path / "watchlist.json"


def test_save_and_load_watchlist(watchlist_file):
    entries = [
        WatchlistEntry(port=22, protocol="tcp", required=True, label="SSH"),
        WatchlistEntry(port=23, protocol="tcp", required=False, label="Telnet"),
    ]
    save_watchlist(watchlist_file, entries)
    loaded = load_watchlist(watchlist_file)
    assert len(loaded) == 2
    assert loaded[0].port == 22
    assert loaded[0].required is True
    assert loaded[0].label == "SSH"
    assert loaded[1].port == 23
    assert loaded[1].required is False


def test_load_watchlist_missing_file(tmp_path):
    result = load_watchlist(tmp_path / "nonexistent.json")
    assert result == []


def test_no_violations_when_compliant(ssh_port, http_port):
    entries = [WatchlistEntry(port=22, required=True)]
    violations = check_watchlist(entries, [ssh_port, http_port])
    assert violations == []


def test_violation_required_port_missing(http_port):
    entries = [WatchlistEntry(port=22, required=True)]
    violations = check_watchlist(entries, [http_port])
    assert len(violations) == 1
    assert violations[0].entry.port == 22
    assert violations[0].actual_port is None
    assert "not open" in violations[0].message


def test_violation_forbidden_port_open(ssh_port, http_port):
    entries = [WatchlistEntry(port=80, required=False)]
    violations = check_watchlist(entries, [ssh_port, http_port])
    assert len(violations) == 1
    assert violations[0].entry.port == 80
    assert violations[0].actual_port == http_port
    assert "Forbidden" in violations[0].message


def test_no_violations_forbidden_port_absent(ssh_port):
    entries = [WatchlistEntry(port=80, required=False)]
    violations = check_watchlist(entries, [ssh_port])
    assert violations == []


def test_multiple_violations(ssh_port):
    entries = [
        WatchlistEntry(port=443, required=True),   # missing
        WatchlistEntry(port=22, required=False),   # present but forbidden
    ]
    violations = check_watchlist(entries, [ssh_port])
    assert len(violations) == 2
