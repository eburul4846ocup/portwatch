"""Tests for portwatch.hostlabel."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from portwatch.hostlabel import (
    get_label,
    list_labels,
    load_labels,
    remove_label,
    save_labels,
    set_label,
)


@pytest.fixture()
def labels_file(tmp_path: Path) -> Path:
    return tmp_path / "hostlabels.json"


def test_load_labels_missing_file(labels_file: Path) -> None:
    assert load_labels(labels_file) == {}


def test_load_labels_invalid_json(labels_file: Path) -> None:
    labels_file.write_text("not-json")
    assert load_labels(labels_file) == {}


def test_load_labels_wrong_type(labels_file: Path) -> None:
    labels_file.write_text("[1, 2, 3]")
    assert load_labels(labels_file) == {}


def test_save_and_load_roundtrip(labels_file: Path) -> None:
    data = {"192.168.1.1": {"label": "router", "role": "network"}}
    save_labels(labels_file, data)
    assert load_labels(labels_file) == data


def test_set_label_creates_entry(labels_file: Path) -> None:
    set_label(labels_file, "10.0.0.1", "webserver", role="web")
    entry = get_label(labels_file, "10.0.0.1")
    assert entry is not None
    assert entry["label"] == "webserver"
    assert entry["role"] == "web"


def test_set_label_no_role(labels_file: Path) -> None:
    set_label(labels_file, "10.0.0.2", "db")
    entry = get_label(labels_file, "10.0.0.2")
    assert entry["role"] is None


def test_set_label_overwrites(labels_file: Path) -> None:
    set_label(labels_file, "10.0.0.1", "old", role="x")
    set_label(labels_file, "10.0.0.1", "new", role="y")
    assert get_label(labels_file, "10.0.0.1")["label"] == "new"


def test_remove_label_existing(labels_file: Path) -> None:
    set_label(labels_file, "10.0.0.5", "temp")
    assert remove_label(labels_file, "10.0.0.5") is True
    assert get_label(labels_file, "10.0.0.5") is None


def test_remove_label_missing(labels_file: Path) -> None:
    assert remove_label(labels_file, "1.2.3.4") is False


def test_list_labels_sorted(labels_file: Path) -> None:
    set_label(labels_file, "192.168.1.2", "b", role=None)
    set_label(labels_file, "10.0.0.1", "a", role="web")
    rows = list_labels(labels_file)
    ips = [r[0] for r in rows]
    assert ips == sorted(ips)
    assert len(rows) == 2


def test_list_labels_empty(labels_file: Path) -> None:
    assert list_labels(labels_file) == []
