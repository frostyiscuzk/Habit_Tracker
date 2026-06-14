"""Reminder domain model.

Reminder objects store which Telegram chat should receive a reminder for which
habit and at what time each day.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Reminder:
    """A scheduled daily Telegram reminder for one habit."""

    habit_id: int
    chat_id: int
    hour: int
    minute: int
    id: int | None = None
    enabled: bool = True
