"""Tests for HabitManager.

Corrector note:
These tests check composition and the service layer. HabitManager is composed
with SQLiteStorage, then the UI and CLI can use manager methods instead of SQL.
"""

from datetime import date

from src.manager import HabitManager


def test_manager_creates_and_completes_habit(tmp_path) -> None:
    """Manager should create a habit, complete it, and summarize it."""

    # Composition is used here: HabitManager creates/uses SQLiteStorage.
    manager = HabitManager(database_path=tmp_path / "habits.db")
    habit = manager.create_habit("Read", "daily")

    # The manager coordinates validation, storage, and analytics summary data.
    manager.complete_habit(habit.id or 0, date(2026, 1, 1))
    summary = manager.dashboard_summary()

    assert summary["active_habits"] == 1
    assert summary["total_completions"] == 1


def test_manager_archives_habit(tmp_path) -> None:
    """Archiving through the manager should hide the habit from active lists."""

    manager = HabitManager(database_path=tmp_path / "habits.db")
    habit = manager.create_habit("Read", "daily")

    manager.archive_habit(habit.id or 0)

    # Active habits exclude archived ones, but the data is still available.
    assert manager.list_habits() == []
    assert len(manager.list_habits(include_archived=True)) == 1
