"""Telegram reminder scheduler.

This module connects persisted Reminder records to APScheduler jobs. It is kept
outside the bot handlers so reminders are a separate responsibility.
"""

from __future__ import annotations

import asyncio
from typing import Any

from .manager import HabitManager
from .reminder import Reminder


class ReminderScheduler:
    """Schedules daily Telegram reminder messages with APScheduler."""

    def __init__(self) -> None:
        """Create a background scheduler only when the bot needs reminders."""

        try:
            from apscheduler.schedulers.background import BackgroundScheduler
        except ImportError as exc:
            raise RuntimeError("Install APScheduler to use reminders.") from exc
        self._scheduler = BackgroundScheduler()

    def start(self) -> None:
        """Start background reminder jobs."""

        if not self._scheduler.running:
            self._scheduler.start()

    def stop(self) -> None:
        """Stop background reminder jobs."""

        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    def schedule_existing_reminders(
        self,
        application: Any,
        manager: HabitManager,
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        """Load reminders from SQLite and schedule each one."""

        for reminder in manager.list_reminders():
            habit = manager.get_habit(reminder.habit_id)
            self.schedule_reminder(application, reminder, habit.name, loop)

    def schedule_reminder(
        self,
        application: Any,
        reminder: Reminder,
        habit_name: str,
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        """Schedule or replace one daily Telegram reminder."""

        self._scheduler.add_job(
            lambda: self._send_reminder(application, reminder, habit_name, loop),
            trigger="cron",
            hour=reminder.hour,
            minute=reminder.minute,
            id=self._job_id(reminder),
            replace_existing=True,
        )

    @staticmethod
    def _send_reminder(
        application: Any,
        reminder: Reminder,
        habit_name: str,
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        """Send the Telegram message from the scheduler thread."""

        message = f"⏰ Reminder: {habit_name}\n\nUse /done {reminder.habit_id} when finished."
        asyncio.run_coroutine_threadsafe(
            application.bot.send_message(chat_id=reminder.chat_id, text=message),
            loop,
        )

    @staticmethod
    def _job_id(reminder: Reminder) -> str:
        """Build a stable APScheduler job id."""

        return f"reminder-{reminder.id or reminder.chat_id}-{reminder.habit_id}"
