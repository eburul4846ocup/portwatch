"""Alert system for portwatch — notifies when ports appear or disappear."""

from __future__ import annotations

import logging
import smtplib
from dataclasses import dataclass, field
from email.message import EmailMessage
from typing import List, Optional

from portwatch.snapshot import PortDiff

logger = logging.getLogger(__name__)


@dataclass
class AlertConfig:
    """Configuration for the alerter."""

    smtp_host: str = "localhost"
    smtp_port: int = 25
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    from_addr: str = "portwatch@localhost"
    to_addrs: List[str] = field(default_factory=list)
    use_tls: bool = False


def _build_email(config: AlertConfig, subject: str, body: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = config.from_addr
    msg["To"] = ", ".join(config.to_addrs)
    msg.set_content(body)
    return msg


def _format_diff_body(diff: PortDiff) -> str:
    lines: List[str] = []
    if diff.added:
        lines.append("NEW PORTS DETECTED:")
        for p in diff.added:
            lines.append(f"  + {p}")
    if diff.removed:
        lines.append("PORTS NO LONGER OPEN:")
        for p in diff.removed:
            lines.append(f"  - {p}")
    return "\n".join(lines)


def send_alert(config: AlertConfig, diff: PortDiff) -> bool:
    """Send an email alert for the given diff.  Returns True on success."""
    if not config.to_addrs:
        logger.warning("No recipients configured; skipping alert.")
        return False

    subject = f"[portwatch] Port change detected ({len(diff.added)} added, {len(diff.removed)} removed)"
    body = _format_diff_body(diff)
    msg = _build_email(config, subject, body)

    try:
        cls = smtplib.SMTP_SSL if config.use_tls else smtplib.SMTP
        with cls(config.smtp_host, config.smtp_port) as smtp:
            if config.smtp_user and config.smtp_password:
                smtp.login(config.smtp_user, config.smtp_password)
            smtp.send_message(msg)
        logger.info("Alert sent to %s", config.to_addrs)
        return True
    except smtplib.SMTPException as exc:
        logger.error("Failed to send alert: %s", exc)
        return False


def log_alert(diff: PortDiff) -> None:
    """Write alert to the Python logging system (always available)."""
    for p in diff.added:
        logger.warning("NEW port open: %s", p)
    for p in diff.removed:
        logger.warning("Port closed: %s", p)
