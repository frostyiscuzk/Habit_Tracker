"""Domain models for the habit tracker.

This file contains the main OOP classes. They describe what a habit and a
completion are before any database or user interface code is involved.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from typing import Iterable


class Periodicity(StrEnum):
    """Allowed schedules for a habit.

    A StrEnum keeps the values readable in the database and UI while still
    giving the code a controlled set of choices.
    """

    DAILY = "daily"
    WEEKLY = "weekly"


@dataclass(frozen=True)
class Completion:
    """A single time when the user marked a habit as done."""

    habit_id: int
    completed_on: date
    note: str = ""
    id: int | None = None


@dataclass
class Habit:
    """A habit the user wants to track.

    This class stores the habit settings and also knows how to check whether
    the habit is complete for a selected day or week.

    Assignment concept: base class. DailyHabit and WeeklyHabit inherit from
    this class to reuse common habit behavior.
    """

    name: str
    periodicity: Periodicity | str
    target_count: int = 1
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    id: int | None = None
    archived: bool = False

    def __post_init__(self) -> None:
        """Clean and validate habit data after the object is created."""

        self.name = self.name.strip()
        self.description = self.description.strip()
        if isinstance(self.periodicity, str):
            self.periodicity = Periodicity(self.periodicity.lower())
        if not self.name:
            raise ValueError("Habit name cannot be empty.")
        if self.target_count < 1:
            raise ValueError("Target count must be at least 1.")

    @property
    def is_daily(self) -> bool:
        """Small helper used by analytics and UI code."""

        return self.periodicity == Periodicity.DAILY

    @property
    def is_weekly(self) -> bool:
        """Small helper used by analytics and UI code."""

        return self.periodicity == Periodicity.WEEKLY

    def is_complete_for(self, completions: Iterable[Completion], day: date) -> bool:
        """Return whether this habit met its target for the relevant period.

        Daily habits count completions on the exact date. Weekly habits count
        all completions in the ISO week that contains the selected date.
        """

        if self.is_daily:
            return DailyHabit(
                id=self.id,
                name=self.name,
                target_count=self.target_count,
                description=self.description,
                created_at=self.created_at,
                archived=self.archived,
            ).is_complete_for(completions, day)
        return WeeklyHabit(
            id=self.id,
            name=self.name,
            target_count=self.target_count,
            description=self.description,
            created_at=self.created_at,
            archived=self.archived,
        ).is_complete_for(completions, day)


class DailyHabit(Habit):
    """Convenience subclass for creating a daily habit.

    Assignment concept: inheritance from Habit.
    """

    def __init__(self, name: str, **kwargs: object) -> None:
        super().__init__(name=name, periodicity=Periodicity.DAILY, **kwargs)

    def is_complete_for(self, completions: Iterable[Completion], day: date) -> bool:
        """Daily habits count completions on the exact selected date."""

        count = sum(1 for completion in completions if completion.completed_on == day)
        return count >= self.target_count


class WeeklyHabit(Habit):
    """Convenience subclass for creating a weekly habit.

    Assignment concept: inheritance from Habit.
    """

    def __init__(self, name: str, **kwargs: object) -> None:
        super().__init__(name=name, periodicity=Periodicity.WEEKLY, **kwargs)

    def is_complete_for(self, completions: Iterable[Completion], day: date) -> bool:
        """Weekly habits count completions inside the selected ISO week."""

        year, week, _ = day.isocalendar()
        count = sum(
            1
            for completion in completions
            if completion.completed_on.isocalendar()[:2] == (year, week)
        )
        return count >= self.target_count
