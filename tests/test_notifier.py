"""Tests for portwatch.notifier."""

from unittest.mock import MagicMock, patch

import pytest

from portwatch.alerter import AlertConfig
from portwatch.notifier import NotifierConfig, _severity_for_diff, dispatch
from portwatch.scanner import PortInfo
from portwatch.snapshot import PortDiff


@pytest.fixture()
def added_diff():
    port = PortInfo(port=8080, protocol="tcp", state="open", service="http-alt")
    return PortDiff(added=[port], removed=[], changed=[])


@pytest.fixture()
def removed_diff():
    port = PortInfo(port=22, protocol="tcp", state="open", service="ssh")
    return PortDiff(added=[], removed=[port], changed=[])


@pytest.fixture()
def empty_diff():
    return PortDiff(added=[], removed=[], changed=[])


def test_severity_added(added_diff):
    assert _severity_for_diff(added_diff) == "warning"


def test_severity_removed(removed_diff):
    assert _severity_for_diff(removed_diff) == "critical"


def test_severity_empty(empty_diff):
    assert _severity_for_diff(empty_diff) == "info"


@patch("portwatch.notifier.log_alert")
def test_dispatch_log_channel(mock_log, added_diff):
    cfg = NotifierConfig(log_alerts=True, channels=["log"])
    dispatch(added_diff, cfg)
    mock_log.assert_called_once_with(added_diff)


@patch("portwatch.notifier.send_alert")
def test_dispatch_email_channel(mock_send, added_diff):
    alert_cfg = AlertConfig(
        smtp_host="localhost",
        smtp_port=25,
        from_addr="a@b.com",
        to_addrs=["c@d.com"],
    )
    cfg = NotifierConfig(alert=alert_cfg, channels=["email"])
    dispatch(added_diff, cfg)
    mock_send.assert_called_once_with(added_diff, alert_cfg)


@patch("portwatch.notifier.send_alert")
def test_dispatch_email_no_alert_config(mock_send, added_diff):
    cfg = NotifierConfig(alert=None, channels=["email"])
    dispatch(added_diff, cfg)  # should not raise
    mock_send.assert_not_called()


@patch("portwatch.notifier.log_alert")
def test_dispatch_below_min_severity(mock_log, added_diff):
    cfg = NotifierConfig(log_alerts=True, channels=["log"], min_severity="critical")
    dispatch(added_diff, cfg)  # warning < critical → skip
    mock_log.assert_not_called()


@patch("portwatch.notifier.log_alert")
def test_dispatch_unknown_channel_does_not_raise(mock_log, added_diff):
    cfg = NotifierConfig(log_alerts=True, channels=["slack", "log"])
    dispatch(added_diff, cfg)  # unknown channel logged, log channel still runs
    mock_log.assert_called_once()
