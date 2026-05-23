"""Service fingerprinting: enrich PortInfo with banner/version data."""

from __future__ import annotations

import socket
from dataclasses import dataclass, field
from typing import Optional

from portwatch.scanner import PortInfo

_BANNER_TIMEOUT = 2.0  # seconds
_MAX_BANNER_BYTES = 256


@dataclass
class Fingerprint:
    port: int
    banner: Optional[str] = None
    version_hint: Optional[str] = None
    extra: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "port": self.port,
            "banner": self.banner,
            "version_hint": self.version_hint,
            "extra": self.extra,
        }


def _extract_version_hint(banner: str) -> Optional[str]:
    """Try to pull a short version string from a raw banner."""
    for line in banner.splitlines():
        line = line.strip()
        if line:
            # Return first non-empty line, truncated
            return line[:80]
    return None


def grab_banner(host: str, port: int, timeout: float = _BANNER_TIMEOUT) -> Optional[str]:
    """Attempt a TCP banner grab on *host*:*port*.

    Returns the decoded banner string or *None* on any failure.
    """
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            sock.settimeout(timeout)
            raw = sock.recv(_MAX_BANNER_BYTES)
        return raw.decode(errors="replace").strip() or None
    except OSError:
        return None


def fingerprint_port(host: str, port_info: PortInfo) -> Fingerprint:
    """Return a :class:`Fingerprint` for *port_info* on *host*."""
    banner = grab_banner(host, port_info.port)
    version_hint = _extract_version_hint(banner) if banner else None
    return Fingerprint(
        port=port_info.port,
        banner=banner,
        version_hint=version_hint,
    )


def fingerprint_ports(
    host: str, ports: list[PortInfo]
) -> dict[int, Fingerprint]:
    """Fingerprint a list of open ports; returns mapping of port -> Fingerprint."""
    return {pi.port: fingerprint_port(host, pi) for pi in ports}
