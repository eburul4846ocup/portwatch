"""Tests for portwatch.baseline."""

import json
from pathlib import Path

import pytest

from portwatch.scanner import PortInfo
from portwatch.baseline import (
    save_baseline,
    load_baseline,
    baseline_exists,
    approve_ports,
    read_baseline_comment,
)


@pytest.fixture()
def sample_ports():
    return [
        PortInfo(port=22, proto="tcp", state="open", service="ssh", pid=None),
        PortInfo(port=80, proto="tcp", state="open", service="http", pid=1234),
    ]


def test_save_and_load_baseline(tmp_path, sample_ports):
    path = tmp_path / "baseline.json"
    save_baseline(sample_ports, path)
    loaded = load_baseline(path)
    assert loaded is not None
    assert len(loaded) == len(sample_ports)
    assert loaded[0].port == 22
    assert loaded[1].port == 80


def test_load_baseline_missing_returns_none(tmp_path):
    path = tmp_path / "nonexistent.json"
    assert load_baseline(path) is None


def test_baseline_exists_false(tmp_path):
    assert not baseline_exists(tmp_path / "nope.json")


def test_baseline_exists_true(tmp_path, sample_ports):
    path = tmp_path / "baseline.json"
    save_baseline(sample_ports, path)
    assert baseline_exists(path)


def test_approve_ports_without_comment(tmp_path, sample_ports):
    path = tmp_path / "baseline.json"
    approve_ports(sample_ports, path=path)
    assert baseline_exists(path)
    meta = path.with_suffix(".meta.json")
    assert not meta.exists()


def test_approve_ports_with_comment(tmp_path, sample_ports):
    path = tmp_path / "baseline.json"
    approve_ports(sample_ports, path=path, comment="initial approval")
    comment = read_baseline_comment(path)
    assert comment == "initial approval"


def test_read_baseline_comment_missing(tmp_path):
    path = tmp_path / "baseline.json"
    assert read_baseline_comment(path) == ""


def test_read_baseline_comment_corrupt(tmp_path):
    path = tmp_path / "baseline.json"
    meta = path.with_suffix(".meta.json")
    meta.write_text("not-json", encoding="utf-8")
    assert read_baseline_comment(path) == ""
