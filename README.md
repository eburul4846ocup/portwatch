# portwatch

> Background daemon that monitors open ports on a host and alerts when unexpected services appear or disappear.

---

## Installation

```bash
pip install portwatch
```

Or install from source:

```bash
git clone https://github.com/youruser/portwatch.git && cd portwatch && pip install .
```

---

## Usage

Start the daemon with a default scan interval of 60 seconds:

```bash
portwatch start
```

Specify a custom interval and alert via email:

```bash
portwatch start --interval 30 --alert email --recipient ops@example.com
```

Take a snapshot of currently open ports to use as the trusted baseline:

```bash
portwatch snapshot
```

Check daemon status or stop it:

```bash
portwatch status
portwatch stop
```

Configuration is stored in `~/.portwatch/config.toml`. Example:

```toml
[daemon]
interval = 60
baseline = "~/.portwatch/baseline.json"

[alerts]
method = "email"
recipient = "ops@example.com"
```

When a new port opens or a known port closes, `portwatch` logs the event and fires the configured alert.

---

## License

This project is licensed under the [MIT License](LICENSE).