"""Tests for portwatch.fingerprint."""

from __future__ import annotations

import socket
from unittest.mock import MagicMock, patch

import pytest

from portwatch.fingerprint import (
    Fingerprint,
    _extract_version_hint,
    fingerprint_port,
    fingerprint_ports,
    grab_banner,
)
from portwatch.scanner import PortInfo


@pytest.fixture
def ssh_port() -> PortInfo:
    return PortInfo(port=22, proto="tcp", service="ssh", state="open")


@pytest.fixture
def http_port() -> PortInfo:
    return PortInfo(port=80, proto="tcp", service="http", state="open")


# --- _extract_version_hint ---

def test_extract_version_hint_returns_first_line():
    banner = "SSH-2.0-OpenSSH_8.9p1\r\nsome extra"
    assert _extract_version_hint(banner) == "SSH-2.0-OpenSSH_8.9p1"


def test_extract_version_hint_empty_banner():
    assert _extract_version_hint("") is None
    assert _extract_version_hint("   \n  ") is None


def test_extract_version_hint_truncates_long_line():
    long_line = "A" * 100
    result = _extract_version_hint(long_line)
    assert len(result) == 80


# --- grab_banner ---

def test_grab_banner_returns_decoded_data():
    mock_sock = MagicMock()
    mock_sock.__enter__ = lambda s: s
    mock_sock.__exit__ = MagicMock(return_value=False)
    mock_sock.recv.return_value = b"SSH-2.0-OpenSSH_8.9\r\n"

    with patch("portwatch.fingerprint.socket.create_connection", return_value=mock_sock):
        result = grab_banner("127.0.0.1", 22)

    assert result == "SSH-2.0-OpenSSH_8.9"


def test_grab_banner_returns_none_on_connection_error():
    with patch(
        "portwatch.fingerprint.socket.create_connection",
        side_effect=OSError("refused"),
    ):
        result = grab_banner("127.0.0.1", 9999)
    assert result is None


def test_grab_banner_returns_none_on_empty_response():
    mock_sock = MagicMock()
    mock_sock.__enter__ = lambda s: s
    mock_sock.__exit__ = MagicMock(return_value=False)
    mock_sock.recv.return_value = b"   "

    with patch("portwatch.fingerprint.socket.create_connection", return_value=mock_sock):
        result = grab_banner("127.0.0.1", 80)
    assert result is None


# --- fingerprint_port ---

def test_fingerprint_port_populates_fields(ssh_port):
    with patch(
        "portwatch.fingerprint.grab_banner",
        return_value="SSH-2.0-OpenSSH_8.9",
    ):
        fp = fingerprint_port("127.0.0.1", ssh_port)

    assert fp.port == 22
    assert fp.banner == "SSH-2.0-OpenSSH_8.9"
    assert fp.version_hint == "SSH-2.0-OpenSSH_8.9"


def test_fingerprint_port_no_banner(ssh_port):
    with patch("portwatch.fingerprint.grab_banner", return_value=None):
        fp = fingerprint_port("127.0.0.1", ssh_port)

    assert fp.banner is None
    assert fp.version_hint is None


# --- fingerprint_ports ---

def test_fingerprint_ports_returns_mapping(ssh_port, http_port):
    def fake_grab(host, port, timeout=2.0):
        return f"banner-{port}"

    with patch("portwatch.fingerprint.grab_banner", side_effect=fake_grab):
        result = fingerprint_ports("127.0.0.1", [ssh_port, http_port])

    assert set(result.keys()) == {22, 80}
    assert result[22].banner == "banner-22"
    assert result[80].banner == "banner-80"


# --- Fingerprint.as_dict ---

def test_fingerprint_as_dict():
    fp = Fingerprint(port=22, banner="SSH-2.0", version_hint="SSH-2.0")
    d = fp.as_dict()
    assert d["port"] == 22
    assert d["banner"] == "SSH-2.0"
    assert d["version_hint"] == "SSH-2.0"
    assert d["extra"] == {}
