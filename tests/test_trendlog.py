"""Tests for portwatch.trendlog."""
import json
import pytest
from pathlib import Path

from portwatch.trendlog import (
    TrendEntry,
    append_trend_entry,
    load_trend_log,
    summarize_trend,
)


@pytest.fixture
def trend_file(tmp_path) -> Path:
    return tmp_path / "trend.json"


def test_append_creates_file(trend_file):
    entry = append_trend_entry(trend_file, added=2, removed=1, changed=0)
    assert trend_file.exists()
    assert isinstance(entry, TrendEntry)
    assert entry.added == 2
    assert entry.removed == 1
    assert entry.changed == 0


def test_append_multiple_entries(trend_file):
    append_trend_entry(trend_file, added=1, removed=0, changed=0)
    append_trend_entry(trend_file, added=0, removed=1, changed=0)
    append_trend_entry(trend_file, added=0, removed=0, changed=3)
    entries = load_trend_log(trend_file)
    assert len(entries) == 3
    assert entries[0].added == 1
    assert entries[1].removed == 1
    assert entries[2].changed == 3


def test_load_missing_file_returns_empty(trend_file):
    entries = load_trend_log(trend_file)
    assert entries == []


def test_load_invalid_json_returns_empty(trend_file):
    trend_file.write_text("not valid json{{")
    entries = load_trend_log(trend_file)
    assert entries == []


def test_max_entries_pruning(trend_file):
    for i in range(10):
        append_trend_entry(trend_file, added=i, removed=0, changed=0, max_entries=5)
    entries = load_trend_log(trend_file)
    assert len(entries) == 5
    assert entries[0].added == 5


def test_summarize_trend_all_quiet(trend_file):
    append_trend_entry(trend_file, added=0, removed=0, changed=0)
    append_trend_entry(trend_file, added=0, removed=0, changed=0)
    summary = summarize_trend(load_trend_log(trend_file))
    assert summary["total_scans"] == 2
    assert summary["noisy_scans"] == 0
    assert summary["total_added"] == 0


def test_summarize_trend_with_activity(trend_file):
    append_trend_entry(trend_file, added=2, removed=1, changed=0)
    append_trend_entry(trend_file, added=0, removed=0, changed=0)
    append_trend_entry(trend_file, added=0, removed=0, changed=1)
    summary = summarize_trend(load_trend_log(trend_file))
    assert summary["total_scans"] == 3
    assert summary["total_added"] == 2
    assert summary["total_removed"] == 1
    assert summary["total_changed"] == 1
    assert summary["noisy_scans"] == 2


def test_entry_total():
    e = TrendEntry(timestamp="2024-01-01T00:00:00+00:00", added=3, removed=2, changed=1)
    assert e.total() == 6


def test_append_creates_parent_dirs(tmp_path):
    nested = tmp_path / "a" / "b" / "trend.json"
    append_trend_entry(nested, added=1, removed=0, changed=0)
    assert nested.exists()
