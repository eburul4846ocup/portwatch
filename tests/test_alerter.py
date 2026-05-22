"""Tests for portwatch.alerter."""

from __future__ import annotations

import smtplib
from unittest.mock import MagicMock, patch

import pytest

from portwatch.alerter import AlertConfig, log_alert, send_alert
from portwatch.scanner import PortInfo
from portwatch.snapshot import PortDiff


@pytest.fixture()
def sample_diff() -> PortDiff:
    added = [PortInfo(port=8080, protocol="tcp", service="http-alt", state="open")]
    removed = [PortInfo(port=21, protocol="tcp", service="ftp", state="open")]
    return PortDiff(added=added, removed=removed)


@pytest.fixture()
def alert_config() -> AlertConfig:
    return AlertConfig(
        smtp_host="smtp.example.com",
        smtp_port=587,
        from_addr="portwatch@example.com",
        to_addrs=["admin@example.com"],
    )


def test_send_alert_success(alert_config: AlertConfig, sample_diff: PortDiff) -> None:
    mock_smtp = MagicMock()
    with patch("portwatch.alerter.smtplib.SMTP", return_value=mock_smtp) as smtp_cls:
        mock_smtp.__enter__ = lambda s: s
        mock_smtp.__exit__ = MagicMock(return_value=False)
        result = send_alert(alert_config, sample_diff)
    assert result is True
    mock_smtp.send_message.assert_called_once()


def test_send_alert_no_recipients(sample_diff: PortDiff) -> None:
    cfg = AlertConfig(to_addrs=[])
    result = send_alert(cfg, sample_diff)
    assert result is False


def test_send_alert_smtp_failure(alert_config: AlertConfig, sample_diff: PortDiff) -> None:
    with patch("portwatch.alerter.smtplib.SMTP", side_effect=smtplib.SMTPException("conn refused")):
        result = send_alert(alert_config, sample_diff)
    assert result is False


def test_send_alert_with_credentials(alert_config: AlertConfig, sample_diff: PortDiff) -> None:
    alert_config.smtp_user = "user"
    alert_config.smtp_password = "secret"
    mock_smtp = MagicMock()
    mock_smtp.__enter__ = lambda s: s
    mock_smtp.__exit__ = MagicMock(return_value=False)
    with patch("portwatch.alerter.smtplib.SMTP", return_value=mock_smtp):
        send_alert(alert_config, sample_diff)
    mock_smtp.login.assert_called_once_with("user", "secret")


def test_log_alert_no_exception(sample_diff: PortDiff) -> None:
    """log_alert should not raise even with a populated diff."""
    log_alert(sample_diff)  # should complete without error


def test_log_alert_empty_diff() -> None:
    log_alert(PortDiff(added=[], removed=[]))  # no-op, no exception
