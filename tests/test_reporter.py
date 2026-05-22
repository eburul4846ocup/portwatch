"""Tests for portwatch.reporter."""

from __future__ import annotations

import json
from datetime import datetime

import pytest

from portwatch.scanner import PortInfo
from portwatch.snapshot import PortDiff
from portwatch.reporter import (
    format_diff_report,
    format_json_report,
    format_port_table,
)

FIXED_TS = datetime(2024, 6, 1, 12, 0, 0)


@pytest.fixture()
def sample_ports():
    return [
        PortInfo(port=22, proto="tcp", state="open", service="ssh"),
        PortInfo(port=80, proto="tcp", state="open", service="http"),
    ]


@pytest.fixture()
def sample_diff():
    added = [PortInfo(port=443, proto="tcp", state="open", service="https")]
    removed = [PortInfo(port=80, proto="tcp", state="open", service="http")]
    return PortDiff(added=added, removed=removed)


def test_format_port_table_contains_headers(sample_ports):
    table = format_port_table(sample_ports)
    assert "PORT" in table
    assert "SERVICE" in table


def test_format_port_table_lists_ports(sample_ports):
    table = format_port_table(sample_ports)
    assert "22" in table
    assert "ssh" in table
    assert "80" in table
    assert "http" in table


def test_format_port_table_empty():
    table = format_port_table([])
    assert "no open ports" in table


def test_format_diff_report_shows_added(sample_diff):
    report = format_diff_report(sample_diff, timestamp=FIXED_TS)
    assert "[+]" in report
    assert "443" in report
    assert "https" in report


def test_format_diff_report_shows_removed(sample_diff):
    report = format_diff_report(sample_diff, timestamp=FIXED_TS)
    assert "[-]" in report
    assert "80" in report


def test_format_diff_report_no_changes():
    diff = PortDiff(added=[], removed=[])
    report = format_diff_report(diff, timestamp=FIXED_TS)
    assert "No changes detected" in report


def test_format_diff_report_timestamp(sample_diff):
    report = format_diff_report(sample_diff, timestamp=FIXED_TS)
    assert "2024-06-01" in report


def test_format_json_report_valid_json(sample_ports):
    output = format_json_report(sample_ports, timestamp=FIXED_TS)
    data = json.loads(output)
    assert data["port_count"] == 2
    assert len(data["ports"]) == 2


def test_format_json_report_fields(sample_ports):
    data = json.loads(format_json_report(sample_ports, timestamp=FIXED_TS))
    first = data["ports"][0]
    assert "port" in first
    assert "proto" in first
    assert "service" in first
    assert "state" in first


def test_format_json_report_timestamp_field(sample_ports):
    data = json.loads(format_json_report(sample_ports, timestamp=FIXED_TS))
    assert data["generated_at"] == "2024-06-01T12:00:00Z"
