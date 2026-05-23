"""Background daemon loop for portwatch."""

from __future__ import annotations

import logging
import signal
import time
from types import FrameType
from typing import Optional

from portwatch.alerter import send_alert
from portwatch.config import WatchConfig
from portwatch.history import append_history_entry
from portwatch.ratelimiter import RateLimiter
from portwatch.scanner import scan_ports
from portwatch.snapshot import load_snapshot, save_snapshot, diff_snapshots

logger = logging.getLogger(__name__)

_running = True


def _handle_signal(signum: int, frame: Optional[FrameType]) -> None:
    global _running
    logger.info("Received signal %d — shutting down.", signum)
    _running = False


def _register_signals() -> None:
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)


def run_once(config: WatchConfig, rate_limiter: Optional[RateLimiter] = None) -> bool:
    """Scan ports once, persist snapshot, alert on changes. Returns True if changes found."""
    current = scan_ports(config.ports)
    previous = load_snapshot(config.snapshot_file)
    diff = diff_snapshots(previous, current)

    if diff.has_changes():
        logger.warning("Port changes detected: +%d -%d", len(diff.added), len(diff.removed))
        append_history_entry(config.history_file, diff, current)

        if config.alert:
            alert_key = "port_change"
            if rate_limiter is None or rate_limiter.is_allowed(alert_key):
                send_alert(config.alert, diff)
                if rate_limiter is not None:
                    rate_limiter.record(alert_key)
            else:
                logger.info("Alert suppressed by rate limiter for key '%s'.", alert_key)

        save_snapshot(config.snapshot_file, current)
        return True

    logger.debug("No port changes detected.")
    save_snapshot(config.snapshot_file, current)
    return False


def run_daemon(config: WatchConfig) -> None:
    """Run the monitoring loop until a termination signal is received."""
    global _running
    _running = True
    _register_signals()

    rate_limiter = RateLimiter(config=config.rate_limit)
    logger.info("portwatch daemon started (interval=%ds).", config.interval_seconds)

    while _running:
        try:
            run_once(config, rate_limiter=rate_limiter)
        except Exception:
            logger.exception("Unexpected error during scan.")
        for _ in range(config.interval_seconds):
            if not _running:
                break
            time.sleep(1)

    logger.info("portwatch daemon stopped.")
