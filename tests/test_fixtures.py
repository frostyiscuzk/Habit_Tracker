"""Tests for the demo dataset used by the dashboard and corrector."""

from datetime import date, timedelta

from src.fixtures import demo_completions, demo_habits


def test_demo_fixtures_cover_five_habits_and_four_weeks() -> None:
    """Demo data should be large enough to show meaningful analytics."""

    today = date(2026, 6, 14)
    habits = demo_habits()
    completions = demo_completions(today=today)

    assert len(habits) == 5
    assert {habit.periodicity.value for habit in habits} == {"daily", "weekly"}
    assert min(completion.completed_on for completion in completions) <= today - timedelta(days=27)
