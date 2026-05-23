"""Tests for portwatch.exporters."""

from __future__ import annotations

import json

import pytest

from portwatch.scanner import PortInfo
from portwatch.snapshot import PortDiff
from portwatch.exporters import export_ports_csv, export_ports_jsonl, export_diff_html


@pytest.fixture()
def sample_ports() -> list:
    return [
        PortInfo(port=22, proto="tcp", state="open", service="ssh", address="0.0.0.0"),
        PortInfo(port=80, proto="tcp", state="open", service="http", address="0.0.0.0"),
    ]


@pytest.fixture()
def sample_diff(sample_ports) -> PortDiff:
    added = [PortInfo(port=443, proto="tcp", state="open", service="https", address="0.0.0.0")]
    removed = [sample_ports[1]]
    return PortDiff(added=added, removed=removed, changed=[])


def test_export_csv_header(sample_ports):
    csv_text = export_ports_csv(sample_ports)
    first_line = csv_text.splitlines()[0]
    assert "port" in first_line
    assert "service" in first_line


def test_export_csv_row_count(sample_ports):
    lines = [l for l in export_ports_csv(sample_ports).splitlines() if l]
    # header + 2 data rows
    assert len(lines) == 3


def test_export_csv_contains_port_numbers(sample_ports):
    csv_text = export_ports_csv(sample_ports)
    assert "22" in csv_text
    assert "80" in csv_text


def test_export_jsonl_valid_json(sample_ports):
    jsonl = export_ports_jsonl(sample_ports)
    objects = [json.loads(line) for line in jsonl.splitlines()]
    assert len(objects) == 2
    assert objects[0]["port"] == 22
    assert objects[1]["service"] == "http"


def test_export_jsonl_empty():
    result = export_ports_jsonl([])
    assert result == ""


def test_export_diff_html_structure(sample_diff):
    html = export_diff_html(sample_diff)
    assert "<!DOCTYPE html>" in html
    assert "<table" in html
    assert "443" in html   # added port
    assert "80" in html    # removed port


def test_export_diff_html_custom_title(sample_diff):
    html = export_diff_html(sample_diff, title="My Custom Title")
    assert "My Custom Title" in html


def test_export_diff_html_css_classes(sample_diff):
    html = export_diff_html(sample_diff)
    assert 'class="added"' in html
    assert 'class="removed"' in html


def test_export_diff_html_empty_diff():
    diff = PortDiff(added=[], removed=[], changed=[])
    html = export_diff_html(diff)
    assert "<table" in html
