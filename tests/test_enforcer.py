"""Tests for portwatch.enforcer."""

from pathlib import Path
from unittest.mock import patch

import pytest

from portwatch.scanner import PortInfo
from portwatch.baseline import save_baseline
from portwatch.enforcer import enforce, BaselineMissingError


@pytest.fixture()
def ssh_port():
    return PortInfo(port=22, proto="tcp", state="open", service="ssh", pid=None)


@pytest.fixture()
def http_port():
    return PortInfo(port=80, proto="tcp", state="open", service="http", pid=1234)


def test_enforce_raises_when_no_baseline(tmp_path):
    path = tmp_path / "baseline.json"
    with pytest.raises(BaselineMissingError):
        enforce(baseline_path=path)


def test_enforce_compliant(tmp_path, ssh_port):
    path = tmp_path / "baseline.json"
    save_baseline([ssh_port], path)
    diff, compliant = enforce(baseline_path=path, ports=[ssh_port])
    assert compliant is True
    assert diff.added == []
    assert diff.removed == []


def test_enforce_detects_added_port(tmp_path, ssh_port, http_port):
    path = tmp_path / "baseline.json"
    save_baseline([ssh_port], path)
    diff, compliant = enforce(baseline_path=path, ports=[ssh_port, http_port])
    assert compliant is False
    assert len(diff.added) == 1
    assert diff.added[0].port == 80


def test_enforce_detects_removed_port(tmp_path, ssh_port, http_port):
    path = tmp_path / "baseline.json"
    save_baseline([ssh_port, http_port], path)
    diff, compliant = enforce(baseline_path=path, ports=[ssh_port])
    assert compliant is False
    assert len(diff.removed) == 1
    assert diff.removed[0].port == 80


def test_enforce_live_scan(tmp_path, ssh_port):
    path = tmp_path / "baseline.json"
    save_baseline([ssh_port], path)
    with patch("portwatch.enforcer.scan_ports", return_value=[ssh_port]):
        diff, compliant = enforce(baseline_path=path)
    assert compliant is True
