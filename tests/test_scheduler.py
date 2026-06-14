"""Tests for Telegram reminder scheduling.

Corrector note:
This proves the reminder scheduler creates APScheduler jobs from Reminder
objects. It does not send Telegram messages during the test.
"""

import asyncio

from src.reminder import Reminder
from src.scheduler import ReminderScheduler, reminder_timezone_name


class FakeBot:
    async def send_message(self, chat_id: int, text: str) -> None:
        return None


class FakeApplication:
    bot = FakeBot()


def test_scheduler_creates_daily_reminder_job() -> None:
    """A Reminder object should become one scheduled APScheduler job."""

    loop = asyncio.new_event_loop()
    scheduler = ReminderScheduler()
    reminder = Reminder(id=5, habit_id=1, chat_id=123, hour=8, minute=30)

    scheduler.schedule_reminder(FakeApplication(), reminder, "Read", loop)

    assert scheduler._scheduler.get_job("reminder-5-1") is not None
    loop.close()


def test_reminder_timezone_defaults_to_berlin(monkeypatch) -> None:
    """Reminder times use the app timezone, defaulting to Europe/Berlin."""

    monkeypatch.delenv("APP_TIMEZONE", raising=False)

    assert reminder_timezone_name() == "Europe/Berlin"
