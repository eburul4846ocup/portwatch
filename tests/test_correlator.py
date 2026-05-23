"""Tests for portwatch.correlator."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from portwatch.correlator import Advisory, CorrelationReport, _load_advisories, correlate
from portwatch.scanner import PortInfo


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def ssh_port() -> PortInfo:
    return PortInfo(port=22, proto="tcp", state="open", service="ssh")


@pytest.fixture()
def http_port() -> PortInfo:
    return PortInfo(port=80, proto="tcp", state="open", service="http")


@pytest.fixture()
def unknown_port() -> PortInfo:
    return PortInfo(port=9999, proto="tcp", state="open", service="unknown")


@pytest.fixture()
def sample_db(tmp_path: Path) -> Path:
    db = [
        {
            "cve_id": "CVE-2023-00001",
            "port": 22,
            "proto": "tcp",
            "service": "ssh",
            "description": "Test SSH advisory.",
            "severity": "high",
        },
        {
            "cve_id": "CVE-2023-00002",
            "port": 80,
            "proto": "tcp",
            "service": "http",
            "description": "Test HTTP advisory.",
            "severity": "medium",
        },
    ]
    p = tmp_path / "advisories.json"
    p.write_text(json.dumps(db))
    return p


# ---------------------------------------------------------------------------
# _load_advisories
# ---------------------------------------------------------------------------

def test_load_advisories_missing_file(tmp_path: Path) -> None:
    result = _load_advisories(tmp_path / "nope.json")
    assert result == []


def test_load_advisories_invalid_json(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text("not json")
    result = _load_advisories(p)
    assert result == []


def test_load_advisories_not_list(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"key": "value"}))
    result = _load_advisories(p)
    assert result == []


def test_load_advisories_returns_entries(sample_db: Path) -> None:
    advisories = _load_advisories(sample_db)
    assert len(advisories) == 2
    assert all(isinstance(a, Advisory) for a in advisories)


# ---------------------------------------------------------------------------
# correlate
# ---------------------------------------------------------------------------

def test_correlate_match(ssh_port: PortInfo, sample_db: Path) -> None:
    report = correlate([ssh_port], db_path=sample_db)
    assert report.has_findings
    assert report.matches[0]["cve_id"] == "CVE-2023-00001"


def test_correlate_no_match(unknown_port: PortInfo, sample_db: Path) -> None:
    report = correlate([unknown_port], db_path=sample_db)
    assert not report.has_findings


def test_correlate_multiple_ports(ssh_port: PortInfo, http_port: PortInfo, sample_db: Path) -> None:
    report = correlate([ssh_port, http_port], db_path=sample_db)
    cves = {m["cve_id"] for m in report.matches}
    assert "CVE-2023-00001" in cves
    assert "CVE-2023-00002" in cves


def test_correlation_report_as_dict(ssh_port: PortInfo, sample_db: Path) -> None:
    report = correlate([ssh_port], db_path=sample_db)
    d = report.as_dict()
    assert "matches" in d
    assert isinstance(d["matches"], list)
