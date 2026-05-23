"""GeoIP lookup for open port remote addresses."""
from __future__ import annotations

import json
import socket
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class GeoInfo:
    ip: str
    country: str = "unknown"
    city: str = "unknown"
    asn: str = "unknown"

    def as_dict(self) -> dict:
        return {
            "ip": self.ip,
            "country": self.country,
            "city": self.city,
            "asn": self.asn,
        }


def _load_cache(cache_path: Path) -> dict:
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_cache(cache_path: Path, cache: dict) -> None:
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(cache, indent=2))
    except OSError:
        pass


def resolve_hostname(ip: str) -> str:
    """Attempt a reverse DNS lookup; return ip on failure."""
    try:
        return socket.gethostbyaddr(ip)[0]
    except (socket.herror, socket.gaierror, OSError):
        return ip


def lookup(ip: str, cache_path: Optional[Path] = None) -> GeoInfo:
    """Return GeoInfo for *ip*, using a local JSON cache when provided."""
    if cache_path is not None:
        cache = _load_cache(cache_path)
        if ip in cache:
            entry = cache[ip]
            return GeoInfo(
                ip=ip,
                country=entry.get("country", "unknown"),
                city=entry.get("city", "unknown"),
                asn=entry.get("asn", "unknown"),
            )

    # Without a real GeoIP database we fall back to hostname-based hints.
    hostname = resolve_hostname(ip)
    info = GeoInfo(ip=ip)
    if hostname != ip:
        parts = hostname.rstrip(".").split(".")
        if len(parts) >= 2:
            info.country = parts[-1].upper()

    if cache_path is not None:
        cache = _load_cache(cache_path)
        cache[ip] = info.as_dict()
        _save_cache(cache_path, cache)

    return info
