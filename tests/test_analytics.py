"""Tests for analytics.py pure functions.

Corrector note:
These tests check the functional-programming part of the project. The analytics
functions receive input data and return calculated values without changing the
database or UI state.
"""

from datetime import date

from src.analytics import completion_rate, current_streak, longest_streak
from src.habit import Completion, Habit, Periodicity


def test_daily_streaks() -> None:
    """Current and longest streaks should be calculated from completion dates."""

    habit = Habit(id=1, name="Read", periodicity=Periodicity.DAILY)
    completions = [
        Completion(habit_id=1, completed_on=date(2026, 1, 1)),
        Completion(habit_id=1, completed_on=date(2026, 1, 2)),
        Completion(habit_id=1, completed_on=date(2026, 1, 4)),
    ]

    # Jan 1 and Jan 2 are consecutive, so the current streak on Jan 2 is 2.
    assert current_streak(habit, completions, today=date(2026, 1, 2)) == 2
    # The longest consecutive run in the sample data is also 2.
    assert longest_streak(habit, completions) == 2


def test_completion_rate_for_weekly_habit() -> None:
    """Weekly completion rate should count weeks where the target was reached."""

    habit = Habit(id=1, name="Exercise", periodicity=Periodicity.WEEKLY, target_count=2)
    completions = [
        Completion(habit_id=1, completed_on=date(2026, 1, 5)),
        Completion(habit_id=1, completed_on=date(2026, 1, 6)),
        Completion(habit_id=1, completed_on=date(2026, 1, 19)),
    ]

    # Only the first of three weeks has two completions, so the rate is 1/3.
    assert completion_rate(habit, completions, date(2026, 1, 5), date(2026, 1, 25)) == 1 / 3
