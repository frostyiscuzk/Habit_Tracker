"""Seed/demo data for tests and local demos.

The demo dataset lets the marker open the dashboard and immediately see charts,
tables, and streaks without manually entering many records.
"""

from __future__ import annotations

from datetime import date, timedelta

from .habit import Completion, Habit, Periodicity


def demo_habits() -> list[Habit]:
    """Return a small mix of daily and weekly example habits."""

    return [
        Habit(id=1, name="Drink water", periodicity=Periodicity.DAILY, target_count=1),
        Habit(id=2, name="Study Python", periodicity=Periodicity.DAILY, target_count=1),
        Habit(id=3, name="Exercise", periodicity=Periodicity.WEEKLY, target_count=3),
        Habit(id=4, name="Plan the week", periodicity=Periodicity.WEEKLY, target_count=1),
        Habit(id=5, name="Review budget", periodicity=Periodicity.WEEKLY, target_count=1),
    ]


def demo_completions(today: date | None = None) -> list[Completion]:
    """Return recent example completion records for the demo habits."""

    today = today or date.today()
    records: list[Completion] = []
    habit_ids = [1, 2, 3, 4, 5]
    for offset in range(28):
        # Generate a realistic but varied four-week history.
        day = today - timedelta(days=offset)
        if offset % 2 != 0:
            records.append(Completion(habit_id=1, completed_on=day))
        if offset % 3 != 0:
            records.append(Completion(habit_id=2, completed_on=day))
        if day.weekday() in {0, 2, 5}:
            records.append(Completion(habit_id=3, completed_on=day))
        if day.weekday() == 0:
            records.append(Completion(habit_id=4, completed_on=day))
        if day.weekday() == 4:
            records.append(Completion(habit_id=5, completed_on=day))
    return [record for record in records if record.habit_id in habit_ids]
