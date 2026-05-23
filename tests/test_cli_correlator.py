"""Tests for portwatch.cli_correlator."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from portwatch.cli_correlator import cmd_correlate
from portwatch.scanner import PortInfo
from portwatch.snapshot import save_snapshot


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_snapshot(tmp_path: Path, ports: list[PortInfo]) -> Path:
    p = tmp_path / "snapshot.json"
    save_snapshot({f"{pi.port}/{pi.proto}": pi for pi in ports}, p)
    return p


def _make_db(tmp_path: Path, entries: list[dict]) -> Path:
    p = tmp_path / "advisories.json"
    p.write_text(json.dumps(entries))
    return p


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_no_matches_exits_zero(tmp_path: Path, capsys) -> None:
    snap = _make_snapshot(tmp_path, [PortInfo(port=9999, proto="tcp", state="open", service="x")])
    db = _make_db(tmp_path, [])
    ns = SimpleNamespace(snapshot=str(snap), db=str(db), format="text")
    cmd_correlate(ns)  # should not raise SystemExit
    out = capsys.readouterr().out
    assert "No advisories" in out


def test_match_exits_one(tmp_path: Path) -> None:
    snap = _make_snapshot(tmp_path, [PortInfo(port=22, proto="tcp", state="open", service="ssh")])
    db = _make_db(tmp_path, [
        {"cve_id": "CVE-TEST", "port": 22, "proto": "tcp",
         "service": "ssh", "description": "Test.", "severity": "high"}
    ])
    ns = SimpleNamespace(snapshot=str(snap), db=str(db), format="text")
    with pytest.raises(SystemExit) as exc_info:
        cmd_correlate(ns)
    assert exc_info.value.code == 1


def test_json_format_output(tmp_path: Path, capsys) -> None:
    snap = _make_snapshot(tmp_path, [PortInfo(port=22, proto="tcp", state="open", service="ssh")])
    db = _make_db(tmp_path, [
        {"cve_id": "CVE-JSON", "port": 22, "proto": "tcp",
         "service": "ssh", "description": "JSON test.", "severity": "medium"}
    ])
    ns = SimpleNamespace(snapshot=str(snap), db=str(db), format="json")
    with pytest.raises(SystemExit):
        cmd_correlate(ns)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "matches" in data
    assert data["matches"][0]["cve_id"] == "CVE-JSON"


def test_text_format_shows_table(tmp_path: Path, capsys) -> None:
    snap = _make_snapshot(tmp_path, [PortInfo(port=80, proto="tcp", state="open", service="http")])
    db = _make_db(tmp_path, [
        {"cve_id": "CVE-TABLE", "port": 80, "proto": "tcp",
         "service": "http", "description": "Table test.", "severity": "low"}
    ])
    ns = SimpleNamespace(snapshot=str(snap), db=str(db), format="text")
    with pytest.raises(SystemExit):
        cmd_correlate(ns)
    out = capsys.readouterr().out
    assert "CVE-TABLE" in out
    assert "CVE ID" in out
