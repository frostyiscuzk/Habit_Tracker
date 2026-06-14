"""Tests for SQLiteStorage.

Corrector note:
These tests check persistence. They use pytest's tmp_path fixture so the tests
create a temporary SQLite database instead of touching the real app database.
"""

from datetime import date

from src.habit import Habit, Periodicity
from src.reminder import Reminder
from src.storage import SQLiteStorage


def test_storage_persists_habits_and_completions(tmp_path) -> None:
    """Saving a habit and completion should be readable from SQLite."""

    # tmp_path keeps this test isolated from data/habits.db.
    storage = SQLiteStorage(tmp_path / "habits.db")
    habit = storage.add_habit(Habit(name="Read", periodicity=Periodicity.DAILY))

    # SQLite assigns the id after inserting the habit.
    assert habit.id is not None
    storage.add_completion(habit.id, date(2026, 1, 1), "chapter 1")

    # Load data back from the database to prove it was persisted.
    loaded = storage.get_habit(habit.id)
    completions = storage.list_completions(habit.id)

    assert loaded is not None
    assert loaded.name == "Read"
    assert len(completions) == 1
    assert completions[0].completed_on == date(2026, 1, 1)


def test_storage_archives_and_filters_habits(tmp_path) -> None:
    """Archived habits should be hidden unless explicitly requested."""

    storage = SQLiteStorage(tmp_path / "habits.db")
    habit = storage.add_habit(Habit(name="Read", periodicity="daily", archived=True))

    # Normal list hides archived habits; include_archived shows them.
    assert storage.list_habits() == []
    assert storage.list_habits(include_archived=True)[0].id == habit.id


def test_storage_persists_reminders(tmp_path) -> None:
    """Reminder settings should be saved in SQLite."""

    storage = SQLiteStorage(tmp_path / "habits.db")
    habit = storage.add_habit(Habit(name="Read", periodicity="daily"))

    reminder = storage.add_reminder(
        Reminder(habit_id=habit.id or 0, chat_id=123, hour=8, minute=30)
    )

    reminders = storage.list_reminders(chat_id=123)

    assert reminder.id is not None
    assert len(reminders) == 1
    assert reminders[0].hour == 8
    assert reminders[0].minute == 30


def test_storage_enforces_foreign_key_cascade(tmp_path) -> None:
    """SQLite should remove child rows when a habit is deleted."""

    storage = SQLiteStorage(tmp_path / "habits.db")
    habit = storage.add_habit(Habit(name="Read", periodicity="daily"))
    storage.add_completion(habit.id or 0, date(2026, 1, 1), "")
    storage.add_reminder(Reminder(habit_id=habit.id or 0, chat_id=123, hour=8, minute=30))

    # This direct delete proves SQLite's ON DELETE CASCADE is actually enabled.
    with storage._connection:
        storage._connection.execute("DELETE FROM habits WHERE id = ?", (habit.id,))

    assert storage.list_completions(habit.id) == []
    assert storage.list_reminders(chat_id=123) == []
