"""Tests for portwatch.cidr_filter and portwatch.cli_cidr."""

from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path

import pytest

from portwatch.cidr_filter import CIDRFilter, load_cidr_filter, save_cidr_filter
from portwatch.cli_cidr import cmd_cidr_add, cmd_cidr_remove, cmd_cidr_list, cmd_cidr_check


@pytest.fixture
def filter_file(tmp_path: Path) -> Path:
    return tmp_path / "cidr.json"


# --- CIDRFilter unit tests ---

def test_is_excluded_ipv4():
    cf = CIDRFilter(excluded=["10.0.0.0/8"])
    assert cf.is_excluded("10.1.2.3")
    assert not cf.is_excluded("192.168.1.1")


def test_is_excluded_ipv6():
    cf = CIDRFilter(excluded=["::1/128"])
    assert cf.is_excluded("::1")
    assert not cf.is_excluded("::2")


def test_is_excluded_invalid_address():
    cf = CIDRFilter(excluded=["10.0.0.0/8"])
    assert not cf.is_excluded("not-an-ip")


def test_malformed_cidr_silently_skipped():
    cf = CIDRFilter(excluded=["bad-cidr", "192.168.0.0/24"])
    assert cf.is_excluded("192.168.0.5")
    assert not cf.is_excluded("10.0.0.1")


# --- Persistence tests ---

def test_save_and_load_roundtrip(filter_file: Path):
    cf = CIDRFilter(excluded=["172.16.0.0/12", "10.0.0.0/8"])
    save_cidr_filter(filter_file, cf)
    loaded = load_cidr_filter(filter_file)
    assert loaded.excluded == cf.excluded
    assert loaded.is_excluded("172.20.1.1")


def test_load_missing_file_returns_empty(filter_file: Path):
    cf = load_cidr_filter(filter_file)
    assert cf.excluded == []


def test_load_invalid_json_returns_empty(filter_file: Path):
    filter_file.write_text("not json")
    cf = load_cidr_filter(filter_file)
    assert cf.excluded == []


def test_load_wrong_type_for_excluded(filter_file: Path):
    filter_file.write_text(json.dumps({"excluded": "10.0.0.0/8"}))
    cf = load_cidr_filter(filter_file)
    assert cf.excluded == []


# --- CLI command tests ---

def test_cmd_cidr_add_creates_entry(filter_file: Path):
    cmd_cidr_add(Namespace(file=str(filter_file), cidr="10.0.0.0/8"))
    cf = load_cidr_filter(filter_file)
    assert "10.0.0.0/8" in cf.excluded


def test_cmd_cidr_add_duplicate_no_duplicate(filter_file: Path, capsys):
    cmd_cidr_add(Namespace(file=str(filter_file), cidr="10.0.0.0/8"))
    cmd_cidr_add(Namespace(file=str(filter_file), cidr="10.0.0.0/8"))
    cf = load_cidr_filter(filter_file)
    assert cf.excluded.count("10.0.0.0/8") == 1


def test_cmd_cidr_remove_existing(filter_file: Path):
    save_cidr_filter(filter_file, CIDRFilter(excluded=["10.0.0.0/8"]))
    cmd_cidr_remove(Namespace(file=str(filter_file), cidr="10.0.0.0/8"))
    cf = load_cidr_filter(filter_file)
    assert "10.0.0.0/8" not in cf.excluded


def test_cmd_cidr_remove_missing_exits_one(filter_file: Path):
    save_cidr_filter(filter_file, CIDRFilter(excluded=[]))
    with pytest.raises(SystemExit) as exc:
        cmd_cidr_remove(Namespace(file=str(filter_file), cidr="10.0.0.0/8"))
    assert exc.value.code == 1


def test_cmd_cidr_list_output(filter_file: Path, capsys):
    save_cidr_filter(filter_file, CIDRFilter(excluded=["192.168.0.0/16"]))
    cmd_cidr_list(Namespace(file=str(filter_file)))
    out = capsys.readouterr().out
    assert "192.168.0.0/16" in out


def test_cmd_cidr_check_excluded_exits_one(filter_file: Path):
    save_cidr_filter(filter_file, CIDRFilter(excluded=["10.0.0.0/8"]))
    with pytest.raises(SystemExit) as exc:
        cmd_cidr_check(Namespace(file=str(filter_file), address="10.5.5.5"))
    assert exc.value.code == 1


def test_cmd_cidr_check_not_excluded(filter_file: Path):
    save_cidr_filter(filter_file, CIDRFilter(excluded=["10.0.0.0/8"]))
    cmd_cidr_check(Namespace(file=str(filter_file), address="8.8.8.8"))  # should not raise
