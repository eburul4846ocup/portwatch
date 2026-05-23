"""Tests for portwatch.anomaly."""
from __future__ import annotations

import pytest

from portwatch.anomaly import (
    AnomalyReport,
    detect_new_high_port,
    detect_trend_spike,
    run_anomaly_checks,
)
from portwatch.scanner import PortInfo
from portwatch.trendlog import TrendEntry
from datetime import datetime, timezone


def _port(port: int, proto: str = "tcp") -> PortInfo:
    return PortInfo(port=port, proto=proto, state="open", service="svc")


def _trend(total: int) -> TrendEntry:
    return TrendEntry(
        timestamp=datetime.now(timezone.utc).isoformat(),
        added=0,
        removed=0,
        total=total,
    )


# --- detect_new_high_port ---

def test_high_port_flagged():
    ports = [_port(8080), _port(22)]
    reports = detect_new_high_port(ports, threshold=1024)
    assert len(reports) == 1
    assert reports[0].port == 8080
    assert reports[0].severity == "medium"


def test_low_ports_not_flagged():
    ports = [_port(22), _port(80), _port(443)]
    reports = detect_new_high_port(ports, threshold=1024)
    assert reports == []


def test_high_port_threshold_respected():
    ports = [_port(500)]
    reports = detect_new_high_port(ports, threshold=100)
    assert len(reports) == 1


# --- detect_trend_spike ---

def test_spike_detected():
    history = [_trend(5), _trend(5), _trend(5)]
    result = detect_trend_spike(history, current_count=15, spike_factor=2.0)
    assert result is not None
    assert result.severity == "high"
    assert "3.0x" in result.reason


def test_no_spike_within_factor():
    history = [_trend(10), _trend(10)]
    result = detect_trend_spike(history, current_count=12, spike_factor=2.0)
    assert result is None


def test_empty_history_returns_none():
    result = detect_trend_spike([], current_count=100)
    assert result is None


def test_zero_average_no_crash():
    history = [_trend(0), _trend(0)]
    result = detect_trend_spike(history, current_count=5)
    assert result is None


# --- run_anomaly_checks ---

def test_run_anomaly_checks_combines_results():
    ports = [_port(22), _port(9999)]
    history = [_trend(1), _trend(1)]
    reports = run_anomaly_checks(ports, history, high_port_threshold=1024, spike_factor=1.5)
    port_reports = [r for r in reports if r.port == 9999]
    spike_reports = [r for r in reports if r.port == 0]
    assert len(port_reports) == 1
    assert len(spike_reports) == 1


def test_run_anomaly_checks_no_anomalies():
    ports = [_port(22), _port(80)]
    history = [_trend(2), _trend(2)]
    reports = run_anomaly_checks(ports, history)
    assert reports == []


# --- AnomalyReport.as_dict ---

def test_as_dict_keys():
    r = AnomalyReport(port=8080, proto="tcp", reason="test", severity="low")
    d = r.as_dict()
    assert set(d.keys()) == {"port", "proto", "reason", "severity"}
