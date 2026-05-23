"""CLI commands for the anomaly-detection feature."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from portwatch.anomaly import run_anomaly_checks
from portwatch.scanner import scan_ports
from portwatch.trendlog import load_trend_log


_DEFAULT_TREND_PATH = Path("portwatch_trend.jsonl")


def cmd_anomaly_scan(args: argparse.Namespace) -> None:
    trend_path = Path(args.trend_file) if args.trend_file else _DEFAULT_TREND_PATH
    history = load_trend_log(trend_path)

    ports = scan_ports()
    reports = run_anomaly_checks(
        ports,
        history,
        high_port_threshold=args.high_port_threshold,
        spike_factor=args.spike_factor,
    )

    if not reports:
        print("No anomalies detected.")
        sys.exit(0)

    if args.format == "json":
        print(json.dumps([r.as_dict() for r in reports], indent=2))
    else:
        print(f"{'PORT':<10} {'PROTO':<6} {'SEV':<8} REASON")
        print("-" * 60)
        for r in reports:
            port_str = str(r.port) if r.port else "*"
            print(f"{port_str:<10} {r.proto:<6} {r.severity:<8} {r.reason}")

    sys.exit(1 if reports else 0)


def register_anomaly_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("anomaly", help="Detect port anomalies")
    p.add_argument(
        "--trend-file",
        default=None,
        help="Path to trend log (default: portwatch_trend.jsonl)",
    )
    p.add_argument(
        "--high-port-threshold",
        type=int,
        default=1024,
        metavar="N",
        help="Flag ports above this number (default: 1024)",
    )
    p.add_argument(
        "--spike-factor",
        type=float,
        default=2.0,
        metavar="F",
        help="Alert when port count exceeds F times historical avg (default: 2.0)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    p.set_defaults(func=cmd_anomaly_scan)
