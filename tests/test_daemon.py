"""Tests for portwatch.daemon (rate-limiter integration)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from portwatch.alerter import AlertConfig
from portwatch.config import WatchConfig
from portwatch.ratelimiter import RateLimitConfig, RateLimiter
from portwatch.scanner import PortInfo
from portwatch.snapshot import PortDiff


@pytest.fixture
def base_config(tmp_path: Path) -> WatchConfig:
    return WatchConfig(
        ports=[22, 80],
        snapshot_file=str(tmp_path / "snap.json"),
        history_file=str(tmp_path / "history.jsonl"),
        rate_limit=RateLimitConfig(
            cooldown_seconds=300,
            state_file=str(tmp_path / "rl.json"),
        ),
    )


@pytest.fixture
def sample_port() -> PortInfo:
    return PortInfo(port=9999, proto="tcp", service="unknown", state="open")


def test_run_once_no_changes(base_config: WatchConfig) -> None:
    from portwatch.daemon import run_once

    empty_diff = PortDiff(added=[], removed=[])
    with patch("portwatch.daemon.scan_ports", return_value=[]), \
         patch("portwatch.daemon.load_snapshot", return_value=[]), \
         patch("portwatch.daemon.diff_snapshots", return_value=empty_diff), \
         patch("portwatch.daemon.save_snapshot") as mock_save:
        result = run_once(base_config)
    assert result is False
    mock_save.assert_called_once()


def test_run_once_with_changes(base_config: WatchConfig, sample_port: PortInfo) -> None:
    from portwatch.daemon import run_once

    diff = PortDiff(added=[sample_port], removed=[])
    with patch("portwatch.daemon.scan_ports", return_value=[sample_port]), \
         patch("portwatch.daemon.load_snapshot", return_value=[]), \
         patch("portwatch.daemon.diff_snapshots", return_value=diff), \
         patch("portwatch.daemon.append_history_entry"), \
         patch("portwatch.daemon.save_snapshot"):
        result = run_once(base_config)
    assert result is True


def test_run_once_sends_email_when_configured(base_config: WatchConfig, sample_port: PortInfo, tmp_path: Path) -> None:
    from portwatch.daemon import run_once

    base_config.alert = AlertConfig(
        smtp_host="localhost", smtp_port=25,
        sender="a@b.com", recipients=["c@d.com"],
    )
    diff = PortDiff(added=[sample_port], removed=[])
    with patch("portwatch.daemon.scan_ports", return_value=[sample_port]), \
         patch("portwatch.daemon.load_snapshot", return_value=[]), \
         patch("portwatch.daemon.diff_snapshots", return_value=diff), \
         patch("portwatch.daemon.append_history_entry"), \
         patch("portwatch.daemon.save_snapshot"), \
         patch("portwatch.daemon.send_alert") as mock_alert:
        run_once(base_config)
    mock_alert.assert_called_once()


def test_run_once_skips_alert_when_rate_limited(base_config: WatchConfig, sample_port: PortInfo, tmp_path: Path) -> None:
    from portwatch.daemon import run_once

    base_config.alert = AlertConfig(
        smtp_host="localhost", smtp_port=25,
        sender="a@b.com", recipients=["c@d.com"],
    )
    rl = RateLimiter(config=base_config.rate_limit)
    rl.record("port_change")  # simulate already fired

    diff = PortDiff(added=[sample_port], removed=[])
    with patch("portwatch.daemon.scan_ports", return_value=[sample_port]), \
         patch("portwatch.daemon.load_snapshot", return_value=[]), \
         patch("portwatch.daemon.diff_snapshots", return_value=diff), \
         patch("portwatch.daemon.append_history_entry"), \
         patch("portwatch.daemon.save_snapshot"), \
         patch("portwatch.daemon.send_alert") as mock_alert:
        run_once(base_config, rate_limiter=rl)
    mock_alert.assert_not_called()
