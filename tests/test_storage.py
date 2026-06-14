"""Tests for SQLiteStorage.

Corrector note:
These tests check persistence. They use pytest's tmp_path fixture so the tests
create a temporary SQLite database instead of touching the real app database.
"""

from datetime import date

from src.habit import Habit, Periodicity
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
