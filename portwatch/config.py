"""Configuration loader for portwatch."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from portwatch.alerter import AlertConfig

DEFAULT_CONFIG_PATH = Path("/etc/portwatch/config.json")


@dataclass
class WatchConfig:
    """Top-level daemon configuration."""

    snapshot_path: Path = Path("/var/lib/portwatch/snapshot.json")
    scan_interval: int = 300  # seconds
    port_range: str = "1-1024"
    alert: AlertConfig = field(default_factory=AlertConfig)
    log_level: str = "INFO"


def _alert_config_from_dict(d: dict) -> AlertConfig:
    return AlertConfig(
        smtp_host=d.get("smtp_host", "localhost"),
        smtp_port=int(d.get("smtp_port", 25)),
        smtp_user=d.get("smtp_user"),
        smtp_password=d.get("smtp_password"),
        from_addr=d.get("from_addr", "portwatch@localhost"),
        to_addrs=d.get("to_addrs", []),
        use_tls=bool(d.get("use_tls", False)),
    )


def load_config(path: Optional[Path] = None) -> WatchConfig:
    """Load configuration from *path* (JSON).  Missing keys use defaults."""
    cfg_path = path or DEFAULT_CONFIG_PATH
    if not cfg_path.exists():
        return WatchConfig()

    try:
        raw = json.loads(cfg_path.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in config file {cfg_path}: {exc}") from exc

    alert_cfg = _alert_config_from_dict(raw.get("alert", {}))
    return WatchConfig(
        snapshot_path=Path(raw.get("snapshot_path", "/var/lib/portwatch/snapshot.json")),
        scan_interval=int(raw.get("scan_interval", 300)),
        port_range=raw.get("port_range", "1-1024"),
        alert=alert_cfg,
        log_level=raw.get("log_level", "INFO"),
    )
