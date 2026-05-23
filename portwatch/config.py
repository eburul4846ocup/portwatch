"""Configuration loading for portwatch."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from portwatch.alerter import AlertConfig
from portwatch.ratelimiter import RateLimitConfig

_DEFAULT_CONFIG_PATH = "/etc/portwatch/config.json"


@dataclass
class WatchConfig:
    ports: List[int] = field(default_factory=list)
    interval_seconds: int = 60
    snapshot_file: str = "/var/lib/portwatch/snapshot.json"
    history_file: str = "/var/lib/portwatch/history.jsonl"
    alert: Optional[AlertConfig] = None
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)


def _alert_config_from_dict(data: Dict[str, Any]) -> AlertConfig:
    return AlertConfig(
        smtp_host=data.get("smtp_host", "localhost"),
        smtp_port=int(data.get("smtp_port", 25)),
        sender=data.get("sender", "portwatch@localhost"),
        recipients=data.get("recipients", []),
        subject_prefix=data.get("subject_prefix", "[portwatch]"),
    )


def _rate_limit_config_from_dict(data: Dict[str, Any]) -> RateLimitConfig:
    return RateLimitConfig(
        cooldown_seconds=int(data.get("cooldown_seconds", 300)),
        state_file=data.get("state_file", "/var/lib/portwatch/ratelimit_state.json"),
    )


def load_config(path: str = _DEFAULT_CONFIG_PATH) -> WatchConfig:
    """Load a WatchConfig from a JSON file.

    Args:
        path: Path to the JSON configuration file.

    Returns:
        A populated WatchConfig instance.

    Raises:
        FileNotFoundError: If the config file does not exist.
        json.JSONDecodeError: If the config file contains invalid JSON.
        ValueError: If required fields contain invalid values.
    """
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    try:
        text = config_path.read_text()
        data: Dict[str, Any] = json.loads(text)
    except json.JSONDecodeError as exc:
        raise json.JSONDecodeError(
            f"Invalid JSON in configuration file {path!r}: {exc.msg}",
            exc.doc,
            exc.pos,
        ) from exc

    alert: Optional[AlertConfig] = None
    if "alert" in data:
        alert = _alert_config_from_dict(data["alert"])

    rate_limit = RateLimitConfig()
    if "rate_limit" in data:
        rate_limit = _rate_limit_config_from_dict(data["rate_limit"])

    return WatchConfig(
        ports=data.get("ports", []),
        interval_seconds=int(data.get("interval_seconds", 60)),
        snapshot_file=data.get("snapshot_file", "/var/lib/portwatch/snapshot.json"),
        history_file=data.get("history_file", "/var/lib/portwatch/history.jsonl"),
        alert=alert,
        rate_limit=rate_limit,
    )
