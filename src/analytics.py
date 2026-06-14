"""Pure analytics functions for habit statistics.

These functions do not read or write the database. They receive objects, do the
calculation, and return results that the manager or dashboard can display.

Assignment concept: functional programming. These functions are pure helper
functions because they calculate results without changing app state.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta

from .habit import Completion, Habit, Periodicity


def completion_count(completions: list[Completion], habit_id: int) -> int:
    """Count how many times one habit has been completed."""

    return sum(1 for completion in completions if completion.habit_id == habit_id)


def completion_rate(
    habit: Habit, completions: list[Completion], start: date, end: date
) -> float:
    """Return the fraction of periods where the habit target was met."""

    periods = _period_starts(habit.periodicity, start, end)
    if not periods:
        return 0.0
    hits = sum(1 for period_start in periods if period_completed(habit, completions, period_start))
    return hits / len(periods)


def current_streak(habit: Habit, completions: list[Completion], today: date | None = None) -> int:
    """Count consecutive completed periods ending at today/current week."""

    cursor = today or date.today()
    streak = 0
    while period_completed(habit, completions, cursor):
        streak += 1
        cursor = _previous_period(habit.periodicity, cursor)
    return streak


def longest_streak(habit: Habit, completions: list[Completion]) -> int:
    """Return longest run of completed daily or weekly periods."""

    habit_completions = [c for c in completions if c.habit_id == habit.id]
    if not habit_completions:
        return 0

    start = min(c.completed_on for c in habit_completions)
    end = max(c.completed_on for c in habit_completions)
    best = 0
    current = 0
    for period_start in _period_starts(habit.periodicity, start, end):
        if period_completed(habit, completions, period_start):
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def period_completed(habit: Habit, completions: list[Completion], day: date) -> bool:
    """Check whether a habit reached its target in the period containing day."""

    habit_completions = [c for c in completions if c.habit_id == habit.id]
    return habit.is_complete_for(habit_completions, day)


def daily_totals(completions: list[Completion], days: int = 30) -> dict[date, int]:
    """Build daily counts for the bar chart in the dashboard."""

    end = date.today()
    start = end - timedelta(days=days - 1)
    totals = {start + timedelta(days=offset): 0 for offset in range(days)}
    counter = Counter(c.completed_on for c in completions if start <= c.completed_on <= end)
    totals.update(counter)
    return totals


def habit_leaderboard(habits: list[Habit], completions: list[Completion]) -> list[dict[str, object]]:
    """Build one analytics row per habit for the dashboard table."""

    rows: list[dict[str, object]] = []
    grouped: dict[int, list[Completion]] = defaultdict(list)
    for completion in completions:
        grouped[completion.habit_id].append(completion)
    for habit in habits:
        if habit.id is None:
            continue
        habit_completions = grouped.get(habit.id, [])
        rows.append(
            {
                "habit": habit.name,
                "count": len(habit_completions),
                "current_streak": current_streak(habit, completions),
                "longest_streak": longest_streak(habit, completions),
            }
        )
    return sorted(rows, key=lambda row: (-int(row["current_streak"]), str(row["habit"])))


def _period_starts(periodicity: Periodicity, start: date, end: date) -> list[date]:
    """Return every daily or weekly period start between two dates."""

    if end < start:
        return []
    if periodicity == Periodicity.DAILY:
        return [start + timedelta(days=offset) for offset in range((end - start).days + 1)]

    cursor = start - timedelta(days=start.weekday())
    final = end - timedelta(days=end.weekday())
    periods = []
    while cursor <= final:
        periods.append(cursor)
        cursor += timedelta(days=7)
    return periods


def _previous_period(periodicity: Periodicity, day: date) -> date:
    """Move one daily or weekly period backwards."""

    if periodicity == Periodicity.DAILY:
        return day - timedelta(days=1)
    return day - timedelta(days=7)
