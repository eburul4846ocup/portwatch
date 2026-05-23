"""CIDR-based filter for excluding ports from scanning/alerting."""

from __future__ import annotations

import ipaddress
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class CIDRFilter:
    """Holds a list of CIDR ranges whose addresses should be excluded."""

    excluded: List[str] = field(default_factory=list)
    _networks: List[ipaddress.IPv4Network | ipaddress.IPv6Network] = field(
        default_factory=list, init=False, repr=False
    )

    def __post_init__(self) -> None:
        self._networks = []
        for cidr in self.excluded:
            try:
                self._networks.append(ipaddress.ip_network(cidr, strict=False))
            except ValueError:
                pass  # silently skip malformed entries

    def is_excluded(self, address: str) -> bool:
        """Return True if *address* falls within any excluded CIDR range."""
        try:
            addr = ipaddress.ip_address(address)
        except ValueError:
            return False
        return any(addr in net for net in self._networks)


def load_cidr_filter(path: Path) -> CIDRFilter:
    """Load a CIDRFilter from a JSON file.

    Expected format::

        {"excluded": ["10.0.0.0/8", "192.168.0.0/16"]}

    Returns an empty CIDRFilter if the file is missing or malformed.
    """
    if not path.exists():
        return CIDRFilter()
    try:
        data = json.loads(path.read_text())
        excluded = data.get("excluded", [])
        if not isinstance(excluded, list):
            return CIDRFilter()
        return CIDRFilter(excluded=[str(e) for e in excluded])
    except (json.JSONDecodeError, AttributeError):
        return CIDRFilter()


def save_cidr_filter(path: Path, cidr_filter: CIDRFilter) -> None:
    """Persist a CIDRFilter to *path* as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"excluded": cidr_filter.excluded}, indent=2))
