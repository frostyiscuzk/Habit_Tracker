"""Application coordinator between UI, domain objects, and storage.

The manager is the service layer. The dashboard and CLI call this class instead
of talking directly to SQLite, which keeps the user interface code simpler.
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from . import analytics
from .habit import Completion, Habit, Periodicity
from .reminder import Reminder
from .storage import SQLiteStorage


class HabitManager:
    """High-level API used by the dashboard, CLI, and optional bot.

    Assignment concept: composition. HabitManager is composed with a
    SQLiteStorage object and delegates database work to it.
    """

    def __init__(self, storage: SQLiteStorage | None = None, database_path: str | Path | None = None) -> None:
        """Use an existing storage object for tests, or create SQLite storage."""

        # Composition: the manager owns/uses a storage object instead of
        # inheriting from storage or writing SQL in the UI.
        self.storage = storage or SQLiteStorage(database_path)

    def create_habit(
        self,
        name: str,
        periodicity: Periodicity | str,
        target_count: int = 1,
        description: str = "",
    ) -> Habit:
        """Create and save a new habit from UI or CLI input."""

        return self.storage.add_habit(
            Habit(
                name=name,
                periodicity=periodicity,
                target_count=target_count,
                description=description,
            )
        )

    def update_habit(
        self,
        habit_id: int,
        name: str,
        periodicity: Periodicity | str,
        target_count: int,
        description: str,
        archived: bool = False,
    ) -> Habit:
        """Edit an existing habit and validate the edited values."""

        habit = self.get_habit(habit_id)
        habit.name = name
        habit.periodicity = Periodicity(periodicity)
        habit.target_count = target_count
        habit.description = description
        habit.archived = archived
        habit.__post_init__()
        return self.storage.update_habit(habit)

    def archive_habit(self, habit_id: int, archived: bool = True) -> Habit:
        """Hide a habit without deleting its historical completions."""

        habit = self.get_habit(habit_id)
        habit.archived = archived
        return self.storage.update_habit(habit)

    def delete_habit(self, habit_id: int) -> None:
        """Permanently remove a habit and its completions."""

        self.storage.delete_habit(habit_id)

    def get_habit(self, habit_id: int) -> Habit:
        """Load one habit and raise a clear error if it does not exist."""

        habit = self.storage.get_habit(habit_id)
        if habit is None:
            raise ValueError(f"No habit found with id {habit_id}.")
        return habit

    def list_habits(self, include_archived: bool = False) -> list[Habit]:
        """Return habits for display in the UI."""

        return self.storage.list_habits(include_archived=include_archived)

    def complete_habit(
        self, habit_id: int, completed_on: date | None = None, note: str = ""
    ) -> Completion:
        """Mark a habit complete on a given date, defaulting to today."""

        self.get_habit(habit_id)
        return self.storage.add_completion(habit_id, completed_on or date.today(), note)

    def list_completions(
        self,
        habit_id: int | None = None,
        start: date | None = None,
        end: date | None = None,
    ) -> list[Completion]:
        """Return completion records, optionally filtered by habit and date range."""

        return self.storage.list_completions(habit_id=habit_id, start=start, end=end)

    def dashboard_summary(self) -> dict[str, object]:
        """Build all metric values needed by the Streamlit dashboard."""

        habits = self.list_habits()
        completions = self.list_completions()
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        completed_today = sum(1 for c in completions if c.completed_on == today)
        completed_this_week = sum(1 for c in completions if week_start <= c.completed_on <= today)
        return {
            "active_habits": len(habits),
            "completed_today": completed_today,
            "completed_this_week": completed_this_week,
            "total_completions": len(completions),
            "leaderboard": analytics.habit_leaderboard(habits, completions),
            "daily_totals": analytics.daily_totals(completions),
        }

    def seed_demo_data(self) -> None:
        """Load sample habits and completions for screenshots or marking."""

        from .fixtures import demo_completions, demo_habits

        self.storage.replace_demo_data(demo_habits(), demo_completions())

    def add_reminder(
        self, habit_id: int, chat_id: int, hour: int, minute: int
    ) -> Reminder:
        """Create or update a daily Telegram reminder for a habit."""

        self.get_habit(habit_id)
        if not 0 <= hour <= 23:
            raise ValueError("Reminder hour must be between 00 and 23.")
        if not 0 <= minute <= 59:
            raise ValueError("Reminder minute must be between 00 and 59.")
        return self.storage.add_reminder(
            Reminder(habit_id=habit_id, chat_id=chat_id, hour=hour, minute=minute)
        )

    def list_reminders(self, chat_id: int | None = None) -> list[Reminder]:
        """List active reminder settings."""

        return self.storage.list_reminders(chat_id=chat_id)

    def delete_reminder(self, reminder_id: int, chat_id: int | None = None) -> None:
        """Delete one reminder."""

        self.storage.delete_reminder(reminder_id, chat_id=chat_id)
