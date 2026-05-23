"""Tests for portwatch.ratelimiter."""

import json
import time
from pathlib import Path

import pytest

from portwatch.ratelimiter import RateLimitConfig, RateLimiter


@pytest.fixture
def state_file(tmp_path: Path) -> Path:
    return tmp_path / "ratelimit_state.json"


@pytest.fixture
def limiter(state_file: Path) -> RateLimiter:
    cfg = RateLimitConfig(cooldown_seconds=60, state_file=str(state_file))
    return RateLimiter(config=cfg)


def test_initially_allowed(limiter: RateLimiter) -> None:
    assert limiter.is_allowed("port_added") is True


def test_not_allowed_after_record(limiter: RateLimiter) -> None:
    limiter.record("port_added")
    assert limiter.is_allowed("port_added") is False


def test_allowed_after_cooldown(limiter: RateLimiter, state_file: Path) -> None:
    past = time.time() - 120
    state_file.write_text(json.dumps({"port_added": past}))
    limiter._load_state()
    assert limiter.is_allowed("port_added") is True


def test_state_persisted(limiter: RateLimiter, state_file: Path) -> None:
    limiter.record("port_removed")
    data = json.loads(state_file.read_text())
    assert "port_removed" in data


def test_reset_single_key(limiter: RateLimiter) -> None:
    limiter.record("port_added")
    limiter.record("port_removed")
    limiter.reset("port_added")
    assert limiter.is_allowed("port_added") is True
    assert limiter.is_allowed("port_removed") is False


def test_reset_all_keys(limiter: RateLimiter) -> None:
    limiter.record("port_added")
    limiter.record("port_removed")
    limiter.reset()
    assert limiter.is_allowed("port_added") is True
    assert limiter.is_allowed("port_removed") is True


def test_load_invalid_state_file(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("not-json")
    cfg = RateLimitConfig(cooldown_seconds=60, state_file=str(bad_file))
    limiter = RateLimiter(config=cfg)
    assert limiter.is_allowed("anything") is True


def test_different_keys_independent(limiter: RateLimiter) -> None:
    limiter.record("key_a")
    assert limiter.is_allowed("key_a") is False
    assert limiter.is_allowed("key_b") is True
