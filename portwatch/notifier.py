"""Notifier module: dispatches alerts via configured channels (email, log)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

from portwatch.alerter import AlertConfig, send_alert, log_alert
from portwatch.snapshot import PortDiff

logger = logging.getLogger(__name__)


@dataclass
class NotifierConfig:
    """Aggregated notification configuration."""

    alert: Optional[AlertConfig] = None
    log_alerts: bool = True
    min_severity: str = "info"  # info | warning | critical
    channels: List[str] = field(default_factory=lambda: ["log"])


def _severity_for_diff(diff: PortDiff) -> str:
    """Derive a severity label from the diff contents."""
    if diff.removed:
        return "critical"
    if diff.added:
        return "warning"
    return "info"


def _severity_rank(severity: str) -> int:
    return {"info": 0, "warning": 1, "critical": 2}.get(severity, 0)


def dispatch(diff: PortDiff, config: NotifierConfig) -> None:
    """Send notifications for *diff* according to *config*.

    Channels are processed in order; failures in one channel do not prevent
    others from running.
    """
    severity = _severity_for_diff(diff)

    if _severity_rank(severity) < _severity_rank(config.min_severity):
        logger.debug(
            "Skipping notification: severity %s below minimum %s",
            severity,
            config.min_severity,
        )
        return

    for channel in config.channels:
        if channel == "log":
            if config.log_alerts:
                try:
                    log_alert(diff)
                except Exception as exc:  # pragma: no cover
                    logger.error("log_alert failed: %s", exc)

        elif channel == "email":
            if config.alert is not None:
                try:
                    send_alert(diff, config.alert)
                except Exception as exc:
                    logger.error("send_alert failed: %s", exc)
            else:
                logger.warning("Email channel requested but no AlertConfig provided.")

        else:
            logger.warning("Unknown notification channel: %s", channel)
