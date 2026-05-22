"""Port scanner module for detecting open ports on the local host."""

import socket
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PortInfo:
    """Represents a single open port with associated metadata."""

    port: int
    protocol: str  # 'tcp' or 'udp'
    service: Optional[str] = field(default=None)
    state: str = "open"

    def __str__(self) -> str:
        svc = self.service or "unknown"
        return f"{self.protocol.upper()}:{self.port} ({svc})"


def resolve_service(port: int, protocol: str) -> Optional[str]:
    """Try to resolve a well-known service name for a given port/protocol."""
    try:
        return socket.getservbyport(port, protocol)
    except OSError:
        return None


def scan_tcp_ports(host: str = "127.0.0.1", port_range: tuple[int, int] = (1, 65535)) -> list[PortInfo]:
    """Scan TCP ports in the given range on the specified host."""
    open_ports: list[PortInfo] = []
    start, end = port_range

    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.1)
            try:
                result = sock.connect_ex((host, port))
                if result == 0:
                    service = resolve_service(port, "tcp")
                    open_ports.append(PortInfo(port=port, protocol="tcp", service=service))
                    logger.debug("Found open TCP port: %d (%s)", port, service or "unknown")
            except OSError as exc:
                logger.warning("Error scanning TCP port %d: %s", port, exc)

    return open_ports


def scan_ports(host: str = "127.0.0.1", port_range: tuple[int, int] = (1, 1024)) -> list[PortInfo]:
    """Entry point for scanning open ports. Returns a list of PortInfo objects."""
    logger.info("Starting port scan on %s, range %d-%d", host, *port_range)
    results = scan_tcp_ports(host, port_range)
    logger.info("Scan complete. Found %d open port(s).", len(results))
    return results
