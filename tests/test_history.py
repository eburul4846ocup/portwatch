"""Tests for portwatch.history and the history summary formatter."""

import json
import os
from datetime import datetime

import pytest

from portwatch.history import append_history_entry, load_history
from portwatch.reporter import format_history_summary
from portwatch.scanner import PortInfo


@pytest.fixture()
def sample_ports():
    return [
        PortInfo(port=22, proto="tcp", service="ssh", state="open"),
        PortInfo(port=80, proto="tcp", service="http", state="open"),
    ]


@pytest.fixture()
def history_file(tmp_path):
    return str(tmp_path / "history.jsonl")


def test_append_and_load_single_entry(history_file, sample_ports):
    ts = datetime(2024, 1, 15, 12, 0, 0)
    append_history_entry(history_file, sample_ports, timestamp=ts)

    entries = load_history(history_file)
    assert len(entries) == 1
    assert entries[0]["timestamp"] == ts
    assert len(entries[0]["ports"]) == 2
    ports = {p.port for p in entries[0]["ports"]}
    assert ports == {22, 80}


def test_append_multiple_entries(history_file, sample_ports):
    for day in range(1, 4):
        ts = datetime(2024, 1, day, 0, 0, 0)
        append_history_entry(history_file, sample_ports, timestamp=ts)

    entries = load_history(history_file)
    assert len(entries) == 3
    assert entries[0]["timestamp"] < entries[2]["timestamp"]


def test_load_history_missing_file(history_file):
    entries = load_history("/nonexistent/path/history.jsonl")
    assert entries == []


def test_load_history_with_limit(history_file, sample_ports):
    for day in range(1, 6):
        append_history_entry(history_file, sample_ports, timestamp=datetime(2024, 1, day))

    entries = load_history(history_file, limit=3)
    assert len(entries) == 3
    # Should be the last 3
    assert entries[0]["timestamp"] == datetime(2024, 1, 3)


def test_load_history_skips_corrupt_lines(history_file, sample_ports):
    append_history_entry(history_file, sample_ports, timestamp=datetime(2024, 1, 1))
    with open(history_file, "a") as fh:
        fh.write("not valid json\n")
    append_history_entry(history_file, sample_ports, timestamp=datetime(2024, 1, 2))

    entries = load_history(history_file)
    assert len(entries) == 2


def test_format_history_summary_empty():
    result = format_history_summary([])
    assert "No history" in result


def test_format_history_summary_shows_counts(sample_ports):
    entries = [
        {"timestamp": datetime(2024, 1, 1, 10, 0, 0), "ports": sample_ports},
        {"timestamp": datetime(2024, 1, 2, 10, 0, 0), "ports": sample_ports[:1]},
    ]
    result = format_history_summary(entries)
    assert "2024-01-01" in result
    assert "2" in result
    assert "1" in result
