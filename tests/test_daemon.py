"""Tests for portwatch.daemon."""

from unittest.mock import MagicMock, patch

import pytest

from portwatch.daemon import run_once
from portwatch.scanner import PortInfo
from portwatch.snapshot import PortDiff
from portwatch.config import WatchConfig
from portwatch.alerter import AlertConfig


@pytest.fixture()
def base_config(tmp_path):
    return WatchConfig(
        host="127.0.0.1",
        port_range=(1, 1024),
        interval=60,
        snapshot_path=str(tmp_path / "snap.json"),
        alert=None,
    )


@pytest.fixture()
def sample_port():
    return PortInfo(port=80, protocol="tcp", service="http", state="open")


def test_run_once_no_changes(base_config, sample_port):
    ports = [sample_port]
    diff = PortDiff(added=[], removed=[])

    with patch("portwatch.daemon.scan_ports", return_value=ports), \
         patch("portwatch.daemon.load_snapshot", return_value=ports), \
         patch("portwatch.daemon.compute_diff", return_value=diff), \
         patch("portwatch.daemon.save_snapshot") as mock_save:
        result = run_once(base_config)

    assert result is False
    mock_save.assert_called_once()


def test_run_once_with_changes(base_config, sample_port):
    new_port = PortInfo(port=443, protocol="tcp", service="https", state="open")
    diff = PortDiff(added=[new_port], removed=[])

    with patch("portwatch.daemon.scan_ports", return_value=[sample_port, new_port]), \
         patch("portwatch.daemon.load_snapshot", return_value=[sample_port]), \
         patch("portwatch.daemon.compute_diff", return_value=diff), \
         patch("portwatch.daemon.log_alert") as mock_log, \
         patch("portwatch.daemon.send_alert") as mock_send, \
         patch("portwatch.daemon.save_snapshot"):
        result = run_once(base_config)

    assert result is True
    mock_log.assert_called_once_with(diff)
    mock_send.assert_not_called()  # no alert config


def test_run_once_sends_email_when_configured(base_config, sample_port):
    base_config.alert = AlertConfig(
        smtp_host="smtp.example.com",
        smtp_port=587,
        sender="a@example.com",
        recipients=["b@example.com"],
    )
    diff = PortDiff(added=[sample_port], removed=[])

    with patch("portwatch.daemon.scan_ports", return_value=[sample_port]), \
         patch("portwatch.daemon.load_snapshot", return_value=[]), \
         patch("portwatch.daemon.compute_diff", return_value=diff), \
         patch("portwatch.daemon.log_alert"), \
         patch("portwatch.daemon.send_alert") as mock_send, \
         patch("portwatch.daemon.save_snapshot"):
        run_once(base_config)

    mock_send.assert_called_once_with(base_config.alert, diff)
