"""Tests for portwatch.cli_anomaly."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from portwatch.cli_anomaly import cmd_anomaly_scan, register_anomaly_commands
from portwatch.anomaly import AnomalyReport
from portwatch.scanner import PortInfo


def _ns(**kwargs) -> argparse.Namespace:
    defaults = {
        "trend_file": None,
        "high_port_threshold": 1024,
        "spike_factor": 2.0,
        "format": "text",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@patch("portwatch.cli_anomaly.scan_ports", return_value=[])
@patch("portwatch.cli_anomaly.load_trend_log", return_value=[])
def test_no_anomalies_exits_zero(mock_trend, mock_scan, capsys):
    with pytest.raises(SystemExit) as exc:
        cmd_anomaly_scan(_ns())
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "No anomalies" in out


@patch(
    "portwatch.cli_anomaly.run_anomaly_checks",
    return_value=[
        AnomalyReport(port=8080, proto="tcp", reason="High port", severity="medium")
    ],
)
@patch("portwatch.cli_anomaly.scan_ports", return_value=[])
@patch("portwatch.cli_anomaly.load_trend_log", return_value=[])
def test_anomalies_exits_one(mock_trend, mock_scan, mock_check, capsys):
    with pytest.raises(SystemExit) as exc:
        cmd_anomaly_scan(_ns())
    assert exc.value.code == 1


@patch(
    "portwatch.cli_anomaly.run_anomaly_checks",
    return_value=[
        AnomalyReport(port=8080, proto="tcp", reason="High port", severity="medium")
    ],
)
@patch("portwatch.cli_anomaly.scan_ports", return_value=[])
@patch("portwatch.cli_anomaly.load_trend_log", return_value=[])
def test_json_format_output(mock_trend, mock_scan, mock_check, capsys):
    with pytest.raises(SystemExit):
        cmd_anomaly_scan(_ns(format="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    assert data[0]["port"] == 8080


@patch(
    "portwatch.cli_anomaly.run_anomaly_checks",
    return_value=[
        AnomalyReport(port=8080, proto="tcp", reason="High port", severity="medium")
    ],
)
@patch("portwatch.cli_anomaly.scan_ports", return_value=[])
@patch("portwatch.cli_anomaly.load_trend_log", return_value=[])
def test_text_format_contains_port(mock_trend, mock_scan, mock_check, capsys):
    with pytest.raises(SystemExit):
        cmd_anomaly_scan(_ns(format="text"))
    out = capsys.readouterr().out
    assert "8080" in out
    assert "medium" in out


def test_register_anomaly_commands_adds_subparser():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_anomaly_commands(sub)
    args = parser.parse_args(["anomaly", "--format", "json"])
    assert args.format == "json"
