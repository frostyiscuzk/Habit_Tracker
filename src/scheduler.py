"""Optional reminder scheduler for future notifications.

This module is prepared for reminders. It is separate from the core app so the
habit tracker works even when reminders are not used.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime


class ReminderScheduler:
    """Tiny adapter around APScheduler when reminders are needed."""

    def __init__(self) -> None:
        """Import APScheduler only when reminders are actually created."""

        try:
            from apscheduler.schedulers.background import BackgroundScheduler
        except ImportError as exc:
            raise RuntimeError("Install APScheduler to use reminders.") from exc
        self._scheduler = BackgroundScheduler()

    def start(self) -> None:
        """Start background reminder jobs."""

        self._scheduler.start()

    def stop(self) -> None:
        """Stop background reminder jobs."""

        self._scheduler.shutdown(wait=False)

    def add_daily_reminder(
        self, name: str, hour: int, minute: int, callback: Callable[[], None]
    ) -> None:
        """Schedule one daily callback at the requested hour and minute."""

        self._scheduler.add_job(
            callback,
            trigger="cron",
            hour=hour,
            minute=minute,
            id=name,
            replace_existing=True,
            next_run_time=datetime.now(),
        )
