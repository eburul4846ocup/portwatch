# Tag Store — Integration Notes

## Overview

The **tag store** lets operators attach free-form labels (tags) to individual
ports so that reports, alerts, and dashboards can surface human-readable
context alongside raw port numbers.

Tags are stored in a JSON file (default `/var/lib/portwatch/tags.json`).

## CLI Commands

| Command | Description |
|---------|-------------|
| `portwatch tag-add <proto> <port> <tag>` | Add a tag to a port |
| `portwatch tag-remove <proto> <port> <tag>` | Remove a tag from a port |
| `portwatch tag-list <proto> <port>` | List all tags on a port |
| `portwatch tag-find <tag>` | Find all ports carrying a tag |

All commands accept `--tags-file PATH` to override the default location.

## Example

```bash
# Mark SSH as critical
portwatch tag-add tcp 22 critical
portwatch tag-add tcp 22 ssh

# Mark web services
portwatch tag-add tcp 80 web
portwatch tag-add tcp 443 web
portwatch tag-add tcp 443 tls

# Find everything marked critical
portwatch tag-find critical
#   tcp:22

# Remove a tag
portwatch tag-remove tcp 22 critical
```

## Integration with `cli.py`

Register the sub-commands in `portwatch/cli.py` inside `build_parser`:

```python
from portwatch.cli_tagstore import register_tagstore_commands

register_tagstore_commands(sub, default_path=str(cfg_dir / "tags.json"))
```

## File Format

```json
{
  "tcp:22": ["ssh", "critical"],
  "tcp:443": ["https", "tls", "web"]
}
```

Keys follow the pattern `<proto>:<port>`.  Values are arrays of tag strings.
The file is human-editable.
