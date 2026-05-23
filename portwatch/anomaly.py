"""Anomaly detection: flag ports that deviate from historical norms."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from portwatch.scanner import PortInfo
from portwatch.trendlog import TrendEntry


@dataclass
class AnomalyReport:
    port: int
    proto: str
    reason: str
    severity: str  # "low" | "medium" | "high"

    def as_dict(self) -> dict:
        return {
            "port": self.port,
            "proto": self.proto,
            "reason": self.reason,
            "severity": self.severity,
        }


def _port_key(port: int, proto: str) -> str:
    return f"{port}/{proto}"


def detect_new_high_port(ports: List[PortInfo], threshold: int = 1024) -> List[AnomalyReport]:
    """Flag newly-seen ports above *threshold* that are uncommon."""
    reports: List[AnomalyReport] = []
    for p in ports:
        if p.port > threshold:
            reports.append(
                AnomalyReport(
                    port=p.port,
                    proto=p.proto,
                    reason=f"High-numbered port {p.port} is open",
                    severity="medium",
                )
            )
    return reports


def detect_trend_spike(
    history: List[TrendEntry],
    current_count: int,
    spike_factor: float = 2.0,
) -> Optional[AnomalyReport]:
    """Return an anomaly if current open-port count is *spike_factor* times the average."""
    if not history:
        return None
    avg = sum(e.total for e in history) / len(history)
    if avg > 0 and current_count >= avg * spike_factor:
        return AnomalyReport(
            port=0,
            proto="any",
            reason=(
                f"Open-port count ({current_count}) is "
                f"{current_count / avg:.1f}x the historical average ({avg:.1f})"
            ),
            severity="high",
        )
    return None


def run_anomaly_checks(
    ports: List[PortInfo],
    history: List[TrendEntry],
    high_port_threshold: int = 1024,
    spike_factor: float = 2.0,
) -> List[AnomalyReport]:
    """Run all anomaly checks and return a combined list of reports."""
    reports: List[AnomalyReport] = []
    reports.extend(detect_new_high_port(ports, high_port_threshold))
    spike = detect_trend_spike(history, len(ports), spike_factor)
    if spike:
        reports.append(spike)
    return reports
