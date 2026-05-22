"""Tests for portwatch.cli."""

import pytest
from unittest.mock import patch, MagicMock

from portwatch.cli import build_parser, main


def test_build_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["run"])
    assert args.command == "run"
    assert args.config == "portwatch.toml"
    assert args.verbose is False


def test_build_parser_custom_config():
    parser = build_parser()
    args = parser.parse_args(["-c", "custom.toml", "scan"])
    assert args.config == "custom.toml"
    assert args.command == "scan"


def test_main_run_calls_daemon():
    with patch("portwatch.cli.run_daemon") as mock_daemon:
        main(["run"])
    mock_daemon.assert_called_once_with("portwatch.toml")


def test_main_scan_no_changes_exits_zero():
    with patch("portwatch.cli.load_config"), \
         patch("portwatch.cli.run_once", return_value=False):
        with pytest.raises(SystemExit) as exc_info:
            main(["scan"])
    assert exc_info.value.code == 0


def test_main_scan_with_changes_exits_one():
    with patch("portwatch.cli.load_config"), \
         patch("portwatch.cli.run_once", return_value=True):
        with pytest.raises(SystemExit) as exc_info:
            main(["scan"])
    assert exc_info.value.code == 1


def test_main_show(capsys):
    from portwatch.scanner import PortInfo
    from portwatch.config import WatchConfig

    cfg = WatchConfig(
        host="127.0.0.1",
        port_range=(1, 1024),
        interval=60,
        snapshot_path="/tmp/snap.json",
        alert=None,
    )
    ports = [PortInfo(port=22, protocol="tcp", service="ssh", state="open")]

    with patch("portwatch.cli.load_config", return_value=cfg), \
         patch("portwatch.cli.load_snapshot", return_value=ports):
        main(["show"])

    captured = capsys.readouterr()
    assert "22" in captured.out
    assert "ssh" in captured.out


def test_main_no_command_exits():
    with pytest.raises(SystemExit) as exc_info:
        main([])
    assert exc_info.value.code == 1
