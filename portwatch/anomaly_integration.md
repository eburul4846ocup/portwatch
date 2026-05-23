# Anomaly Detection Integration

The `portwatch.anomaly` module provides lightweight statistical anomaly detection
for open ports, complementing the snapshot-diff and baseline enforcement features.

## Checks performed

| Check | Description | Default threshold |
|---|---|---|
| High-numbered port | Flags any open port above a configurable threshold | > 1024 |
| Trend spike | Alerts when the current port count is ≥ N× the historical average | 2.0× |

## CLI usage

```bash
# Basic scan (text output)
portwatch anomaly

# Adjust thresholds
portwatch anomaly --high-port-threshold 8000 --spike-factor 1.5

# Machine-readable output
portwatch anomaly --format json

# Custom trend log path
portwatch anomaly --trend-file /var/lib/portwatch/trend.jsonl
```

Exit code `0` means no anomalies; exit code `1` means at least one anomaly was
detected — suitable for use in CI pipelines or cron-based alerting.

## Programmatic API

```python
from portwatch.anomaly import run_anomaly_checks
from portwatch.scanner import scan_ports
from portwatch.trendlog import load_trend_log
from pathlib import Path

ports = scan_ports()
history = load_trend_log(Path("portwatch_trend.jsonl"))
reports = run_anomaly_checks(ports, history)
for r in reports:
    print(r.as_dict())
```

## Adding new checks

Add a function with the signature:

```python
def detect_<name>(ports, ...) -> List[AnomalyReport]:
    ...
```

Then call it inside `run_anomaly_checks` so it is included automatically in
both the CLI and any programmatic callers.
