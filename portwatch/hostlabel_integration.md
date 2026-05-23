# Host Label Integration

The `hostlabel` module lets operators attach a human-readable **label** and optional **role** to any IP address seen during port scans. Labels are stored in a JSON file (default: `/var/lib/portwatch/hostlabels.json`).

## Data model

```json
{
  "192.168.1.1": { "label": "core-router", "role": "network" },
  "10.0.0.5":    { "label": "prod-db-01",  "role": "db" }
}
```

## CLI commands

| Command | Description |
|---|---|
| `label-set <ip> <label> [--role ROLE]` | Create or update a label |
| `label-remove <ip>` | Delete a label entry |
| `label-list` | Print all labels in a table |
| `label-lookup <ip>` | Print the label for a single IP |

All commands accept `--labels-file FILE` to override the default path.

## Example

```bash
portwatch label-set 10.0.0.1 webserver --role web
portwatch label-list
# IP                   LABEL                    ROLE
# --------------------------------------------------------
# 10.0.0.1             webserver                web

portwatch label-lookup 10.0.0.1
# 10.0.0.1: webserver [web]

portwatch label-remove 10.0.0.1
```

## Programmatic use

```python
from pathlib import Path
from portwatch.hostlabel import set_label, get_label, list_labels

path = Path("/var/lib/portwatch/hostlabels.json")
set_label(path, "10.0.0.1", "webserver", role="web")
entry = get_label(path, "10.0.0.1")  # {"label": "webserver", "role": "web"}
rows = list_labels(path)             # [("10.0.0.1", "webserver", "web")]
```

## Integration with reporter

The `format_port_table` function in `reporter.py` can be extended to resolve IP labels via `get_label`, enriching scan output with friendly host names without modifying the core `PortInfo` dataclass.
