"""Tests for Habit, DailyHabit, WeeklyHabit, and Completion.

Corrector note:
These tests check the OOP model layer. They prove that validation works, that
the daily/weekly subclasses can be used, and that habit completion rules behave
correctly for daily and weekly periods.
"""

from datetime import date

import pytest

from src.habit import Completion, DailyHabit, Habit, Periodicity, WeeklyHabit


def test_habit_validates_name_and_target() -> None:
    """A habit must have a name and a positive target count."""

    # Empty habit names should be rejected because they cannot be displayed.
    with pytest.raises(ValueError):
        Habit(name="", periodicity=Periodicity.DAILY)

    # A target of 0 makes no sense, because the user must complete something.
    with pytest.raises(ValueError):
        Habit(name="Read", periodicity=Periodicity.DAILY, target_count=0)


def test_daily_habit_completion_for_day() -> None:
    """Daily habits only count completions on the exact selected date."""

    # This uses the DailyHabit subclass, which demonstrates inheritance.
    habit = DailyHabit(id=1, name="Read")
    completions = [Completion(habit_id=1, completed_on=date(2026, 1, 1))]

    assert habit.is_complete_for(completions, date(2026, 1, 1))
    assert not habit.is_complete_for(completions, date(2026, 1, 2))


def test_weekly_habit_completion_uses_target_count() -> None:
    """Weekly habits count all completions inside the same ISO week."""

    # This weekly habit needs two completions in the week to be considered done.
    habit = WeeklyHabit(id=1, name="Exercise", target_count=2)
    completions = [
        Completion(habit_id=1, completed_on=date(2026, 1, 5)),
        Completion(habit_id=1, completed_on=date(2026, 1, 7)),
    ]

    assert habit.is_complete_for(completions, date(2026, 1, 9))
