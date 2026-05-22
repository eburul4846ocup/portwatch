"""Tests for portwatch.suppressor."""

import json
import os
from datetime import datetime, timedelta, timezone

import pytest

from portwatch.scanner import PortInfo
from portwatch.suppressor import (
    Suppressor,
    SuppressionRule,
    load_suppressions,
    save_suppressions,
)


@pytest.fixture
def ssh_port():
    return PortInfo(port=22, proto="tcp", state="open", service="ssh")


@pytest.fixture
def http_port():
    return PortInfo(port=80, proto="tcp", state="open", service="http")


def future_iso():
    return (datetime.now(tz=timezone.utc) + timedelta(hours=2)).isoformat()


def past_iso():
    return (datetime.now(tz=timezone.utc) - timedelta(hours=1)).isoformat()


# --- SuppressionRule ---

def test_rule_matches_port(ssh_port):
    rule = SuppressionRule(port=22, proto="tcp", reason="planned maintenance")
    assert rule.matches(ssh_port)


def test_rule_does_not_match_different_port(ssh_port):
    rule = SuppressionRule(port=443, proto="tcp", reason="")
    assert not rule.matches(ssh_port)


def test_rule_does_not_match_different_proto(ssh_port):
    rule = SuppressionRule(port=22, proto="udp", reason="")
    assert not rule.matches(ssh_port)


def test_rule_not_expired_when_no_expiry(ssh_port):
    rule = SuppressionRule(port=22, proto="tcp", reason="permanent")
    assert not rule.is_expired()
    assert rule.matches(ssh_port)


def test_rule_expired_in_past(ssh_port):
    rule = SuppressionRule(port=22, proto="tcp", reason="old", expires_at=past_iso())
    assert rule.is_expired()
    assert not rule.matches(ssh_port)


def test_rule_not_expired_in_future(ssh_port):
    rule = SuppressionRule(port=22, proto="tcp", reason="soon", expires_at=future_iso())
    assert not rule.is_expired()
    assert rule.matches(ssh_port)


# --- Suppressor ---

def test_suppressor_is_suppressed(ssh_port):
    rule = SuppressionRule(port=22, proto="tcp", reason="test")
    s = Suppressor(rules=[rule])
    assert s.is_suppressed(ssh_port)


def test_suppressor_not_suppressed(http_port):
    rule = SuppressionRule(port=22, proto="tcp", reason="test")
    s = Suppressor(rules=[rule])
    assert not s.is_suppressed(http_port)


def test_active_rules_excludes_expired():
    expired = SuppressionRule(port=22, proto="tcp", reason="old", expires_at=past_iso())
    active = SuppressionRule(port=80, proto="tcp", reason="current")
    s = Suppressor(rules=[expired, active])
    assert s.active_rules() == [active]


# --- Persistence ---

def test_save_and_load_suppressions(tmp_path):
    path = str(tmp_path / "suppressions.json")
    rule = SuppressionRule(port=8080, proto="tcp", reason="dev server", expires_at=future_iso())
    s = Suppressor(rules=[rule])
    save_suppressions(path, s)

    loaded = load_suppressions(path)
    assert len(loaded.rules) == 1
    assert loaded.rules[0].port == 8080
    assert loaded.rules[0].reason == "dev server"


def test_load_suppressions_missing_file(tmp_path):
    path = str(tmp_path / "nonexistent.json")
    s = load_suppressions(path)
    assert s.rules == []
