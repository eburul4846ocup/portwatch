"""Tests for portwatch.scheduler."""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from portwatch.scheduler import Scheduler, SchedulerConfig, make_scheduler


@pytest.fixture
def cfg() -> SchedulerConfig:
    return SchedulerConfig(interval_seconds=60, jitter_seconds=0)


@pytest.fixture
def scheduler(cfg: SchedulerConfig) -> Scheduler:
    return Scheduler(config=cfg)


def test_due_immediately_on_creation(scheduler: Scheduler) -> None:
    """A freshly created scheduler should be due right away."""
    assert scheduler.due() is True


def test_not_due_after_record_run(scheduler: Scheduler) -> None:
    """After recording a run the scheduler should not be immediately due."""
    scheduler.record_run()
    assert scheduler.due() is False


def test_seconds_until_next_positive_after_run(scheduler: Scheduler) -> None:
    scheduler.record_run()
    remaining = scheduler.seconds_until_next()
    assert 0 < remaining <= 60


def test_seconds_until_next_zero_when_due(scheduler: Scheduler) -> None:
    """When already due, seconds_until_next should return 0."""
    assert scheduler.seconds_until_next() == 0.0


def test_last_run_none_before_first_run(scheduler: Scheduler) -> None:
    assert scheduler.last_run is None


def test_last_run_set_after_record_run(scheduler: Scheduler) -> None:
    before = time.monotonic()
    scheduler.record_run()
    after = time.monotonic()
    assert scheduler.last_run is not None
    assert before <= scheduler.last_run <= after


def test_jitter_applied(cfg: SchedulerConfig) -> None:
    """With jitter configured the next-run offset should vary across calls."""
    cfg.jitter_seconds = 10
    sched = Scheduler(config=cfg)
    offsets: list[float] = []
    for _ in range(20):
        sched._next_run = time.monotonic()  # reset so record_run fires from now
        sched.record_run()
        offsets.append(sched.seconds_until_next())
    # With jitter the values should not all be identical
    assert len(set(round(o, 3) for o in offsets)) > 1


def test_sleep_until_next_calls_sleep(scheduler: Scheduler) -> None:
    scheduler.record_run()
    with patch("portwatch.scheduler.time.sleep") as mock_sleep:
        scheduler.sleep_until_next()
        mock_sleep.assert_called_once()
        args, _ = mock_sleep.call_args
        assert args[0] > 0


def test_sleep_skipped_when_already_due(scheduler: Scheduler) -> None:
    """If the scheduler is already due, sleep should not be called."""
    with patch("portwatch.scheduler.time.sleep") as mock_sleep:
        scheduler.sleep_until_next()
        mock_sleep.assert_not_called()


def test_make_scheduler_factory() -> None:
    sched = make_scheduler(interval=30, jitter=5)
    assert sched.config.interval_seconds == 30
    assert sched.config.jitter_seconds == 5
    assert sched.due() is True
