"""Background daemon loop for portwatch."""

import logging
import signal
import time
from pathlib import Path

from portwatch.alerter import log_alert, send_alert
from portwatch.config import WatchConfig, load_config
from portwatch.scanner import scan_ports
from portwatch.snapshot import load_snapshot, save_snapshot, compute_diff

logger = logging.getLogger(__name__)

_running = True


def _handle_signal(signum, frame):
    global _running
    logger.info("Received signal %s, shutting down.", signum)
    _running = False


def _register_signals():
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)


def run_once(config: WatchConfig) -> bool:
    """Perform a single scan cycle. Returns True if changes were detected."""
    current_ports = scan_ports(
        host=config.host,
        port_range=config.port_range,
    )
    previous_ports = load_snapshot(config.snapshot_path)
    diff = compute_diff(previous_ports, current_ports)

    if diff.has_changes():
        logger.warning(
            "Port changes detected on %s: +%d -%d",
            config.host,
            len(diff.added),
            len(diff.removed),
        )
        log_alert(diff)
        if config.alert:
            send_alert(config.alert, diff)
        save_snapshot(config.snapshot_path, current_ports)
        return True

    logger.debug("No port changes detected on %s.", config.host)
    save_snapshot(config.snapshot_path, current_ports)
    return False


def run_daemon(config_path: str = "portwatch.toml"):
    """Start the daemon loop using the given config file."""
    _register_signals()
    config = load_config(config_path)
    logger.info(
        "portwatch daemon started (host=%s, interval=%ds).",
        config.host,
        config.interval,
    )

    while _running:
        try:
            run_once(config)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Error during scan cycle: %s", exc, exc_info=True)
        time.sleep(config.interval)

    logger.info("portwatch daemon stopped.")
