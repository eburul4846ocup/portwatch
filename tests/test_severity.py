"""Tests for portwatch.severity module."""

from __future__ import annotations

import pytest

from portwatch.scanner import PortInfo
from portwatch.snapshot import PortDiff
from portwatch.severity import Severity, classify_diff


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_port(port: int, proto: str = "tcp", service: str = "unknown") -> PortInfo:
    return PortInfo(port=port, proto=proto, service=service, address="127.0.0.1")


def _diff(added=(), removed=()) -> PortDiff:
    return PortDiff(added=list(added), removed=list(removed))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_no_changes_returns_info():
    report = classify_diff(_diff())
    assert report.severity == Severity.INFO
    assert report.reasons == []


def test_critical_port_added_returns_critical():
    report = classify_diff(_diff(added=[_make_port(23, service="telnet")]))
    assert report.severity == Severity.CRITICAL
    assert any("23" in r for r in report.reasons)


def test_warning_port_added_returns_warning():
    report = classify_diff(_diff(added=[_make_port(22, service="ssh")]))
    assert report.severity == Severity.WARNING


def test_ordinary_port_added_returns_info():
    report = classify_diff(_diff(added=[_make_port(8080, service="http-alt")]))
    assert report.severity == Severity.INFO
    assert len(report.reasons) == 1


def test_port_removed_upgrades_info_to_warning():
    report = classify_diff(_diff(removed=[_make_port(80, service="http")]))
    assert report.severity == Severity.WARNING
    assert any("80" in r for r in report.reasons)


def test_critical_beats_warning():
    report = classify_diff(_diff(
        added=[_make_port(22, service="ssh"), _make_port(3389, service="rdp")]
    ))
    assert report.severity == Severity.CRITICAL


def test_multiple_reasons_recorded():
    report = classify_diff(_diff(
        added=[_make_port(8080), _make_port(9090)],
        removed=[_make_port(80)],
    ))
    assert len(report.reasons) == 3


def test_as_dict_keys():
    report = classify_diff(_diff(added=[_make_port(21)]))
    d = report.as_dict()
    assert "severity" in d
    assert "reasons" in d
    assert d["severity"] == "critical"
