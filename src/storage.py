"""SQLite persistence layer for habits and completion records.

This module is responsible for saving and loading data. The rest of the app can
work with Habit and Completion objects without knowing SQL details.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

from .habit import Completion, Habit, Periodicity
from .reminder import Reminder


DEFAULT_DATABASE_PATH = Path("data/habits.db")


class SQLiteStorage:
    """Small SQLite repository for habits and completions.

    Assignment concept: persistence. This class hides all SQL operations from
    the UI and manager, so the rest of the app works with Python objects.
    """

    def __init__(self, database_path: str | Path | None = None) -> None:
        """Open the database file and create tables if they are missing."""

        self.database_path = Path(
            database_path or os.getenv("DATABASE_PATH") or DEFAULT_DATABASE_PATH
        )
        if self.database_path != Path(":memory:"):
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.database_path)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self.initialize()

    def initialize(self) -> None:
        """Create the database tables used by the app."""

        with self._connection:
            # The habits table stores the habit settings shown in the UI.
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS habits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    periodicity TEXT NOT NULL CHECK(periodicity IN ('daily', 'weekly')),
                    target_count INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    archived INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            # The reminders table stores Telegram reminder settings.
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    habit_id INTEGER NOT NULL,
                    chat_id INTEGER NOT NULL,
                    hour INTEGER NOT NULL,
                    minute INTEGER NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    UNIQUE(habit_id, chat_id),
                    FOREIGN KEY(habit_id) REFERENCES habits(id) ON DELETE CASCADE
                )
                """
            )
            # The completions table stores each date a habit was marked done.
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS completions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    habit_id INTEGER NOT NULL,
                    completed_on TEXT NOT NULL,
                    note TEXT NOT NULL DEFAULT '',
                    UNIQUE(habit_id, completed_on, note),
                    FOREIGN KEY(habit_id) REFERENCES habits(id) ON DELETE CASCADE
                )
                """
            )

    def close(self) -> None:
        """Close the SQLite connection when manual cleanup is needed."""

        self._connection.close()

    def add_habit(self, habit: Habit) -> Habit:
        """Insert a habit and return it with its database id."""

        with self._connection:
            cursor = self._connection.execute(
                """
                INSERT INTO habits
                    (name, description, periodicity, target_count, created_at, archived)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    habit.name,
                    habit.description,
                    habit.periodicity.value,
                    habit.target_count,
                    habit.created_at.isoformat(timespec="seconds"),
                    int(habit.archived),
                ),
            )
        habit.id = int(cursor.lastrowid)
        return habit

    def update_habit(self, habit: Habit) -> Habit:
        """Save edited habit details back to SQLite."""

        if habit.id is None:
            raise ValueError("Cannot update a habit without an id.")
        with self._connection:
            self._connection.execute(
                """
                UPDATE habits
                SET name = ?, description = ?, periodicity = ?, target_count = ?,
                    archived = ?
                WHERE id = ?
                """,
                (
                    habit.name,
                    habit.description,
                    habit.periodicity.value,
                    habit.target_count,
                    int(habit.archived),
                    habit.id,
                ),
            )
        return habit

    def delete_habit(self, habit_id: int) -> None:
        """Delete a habit and its related completions."""

        with self._connection:
            self._connection.execute("DELETE FROM completions WHERE habit_id = ?", (habit_id,))
            self._connection.execute("DELETE FROM reminders WHERE habit_id = ?", (habit_id,))
            self._connection.execute("DELETE FROM habits WHERE id = ?", (habit_id,))

    def get_habit(self, habit_id: int) -> Habit | None:
        """Fetch one habit by id, returning None if it is missing."""

        row = self._connection.execute(
            "SELECT * FROM habits WHERE id = ?", (habit_id,)
        ).fetchone()
        return self._row_to_habit(row) if row else None

    def list_habits(self, include_archived: bool = False) -> list[Habit]:
        """Return habits sorted by name for a stable UI display."""

        if include_archived:
            rows = self._connection.execute(
                "SELECT * FROM habits ORDER BY archived, name COLLATE NOCASE"
            ).fetchall()
        else:
            rows = self._connection.execute(
                """
                SELECT * FROM habits
                WHERE archived = 0
                ORDER BY name COLLATE NOCASE
                """
            ).fetchall()
        return [self._row_to_habit(row) for row in rows]

    def add_completion(
        self, habit_id: int, completed_on: date, note: str = ""
    ) -> Completion:
        """Insert one completion record for a habit and date."""

        with self._connection:
            cursor = self._connection.execute(
                """
                INSERT OR IGNORE INTO completions (habit_id, completed_on, note)
                VALUES (?, ?, ?)
                """,
                (habit_id, completed_on.isoformat(), note.strip()),
            )
        completion_id = int(cursor.lastrowid) if cursor.lastrowid else None
        return Completion(
            id=completion_id,
            habit_id=habit_id,
            completed_on=completed_on,
            note=note.strip(),
        )

    def delete_completion(self, completion_id: int) -> None:
        """Remove one completion record."""

        with self._connection:
            self._connection.execute(
                "DELETE FROM completions WHERE id = ?", (completion_id,)
            )

    def list_completions(
        self,
        habit_id: int | None = None,
        start: date | None = None,
        end: date | None = None,
    ) -> list[Completion]:
        """Return completion records with optional filters."""

        clauses: list[str] = []
        values: list[object] = []
        if habit_id is not None:
            clauses.append("habit_id = ?")
            values.append(habit_id)
        if start is not None:
            clauses.append("completed_on >= ?")
            values.append(start.isoformat())
        if end is not None:
            clauses.append("completed_on <= ?")
            values.append(end.isoformat())
        # Build a small parameterized WHERE clause from the selected filters.
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self._connection.execute(
            f"SELECT * FROM completions {where} ORDER BY completed_on DESC, id DESC",
            values,
        ).fetchall()
        return [self._row_to_completion(row) for row in rows]

    def replace_demo_data(
        self, habits: Iterable[Habit], completions: Iterable[Completion]
    ) -> None:
        """Replace existing data with a complete demo dataset."""

        with self._connection:
            self._connection.execute("DELETE FROM reminders")
            self._connection.execute("DELETE FROM completions")
            self._connection.execute("DELETE FROM habits")
        id_map: dict[int, int] = {}
        for habit in habits:
            # Demo habits have fixed ids, so map them to the new database ids.
            old_id = habit.id
            habit.id = None
            saved = self.add_habit(habit)
            if old_id is not None and saved.id is not None:
                id_map[old_id] = saved.id
        for completion in completions:
            new_habit_id = id_map.get(completion.habit_id, completion.habit_id)
            self.add_completion(new_habit_id, completion.completed_on, completion.note)

    def add_reminder(self, reminder: Reminder) -> Reminder:
        """Insert or update a Telegram reminder for a habit and chat."""

        with self._connection:
            self._connection.execute(
                """
                INSERT INTO reminders (habit_id, chat_id, hour, minute, enabled)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(habit_id, chat_id)
                DO UPDATE SET hour = excluded.hour,
                              minute = excluded.minute,
                              enabled = excluded.enabled
                """,
                (
                    reminder.habit_id,
                    reminder.chat_id,
                    reminder.hour,
                    reminder.minute,
                    int(reminder.enabled),
                ),
            )
        reminder_id = self._find_reminder_id(reminder.habit_id, reminder.chat_id)
        return Reminder(
            id=int(reminder_id),
            habit_id=reminder.habit_id,
            chat_id=reminder.chat_id,
            hour=reminder.hour,
            minute=reminder.minute,
            enabled=reminder.enabled,
        )

    def list_reminders(self, chat_id: int | None = None) -> list[Reminder]:
        """Return reminder settings, optionally for one Telegram chat."""

        if chat_id is None:
            rows = self._connection.execute(
                "SELECT * FROM reminders WHERE enabled = 1 ORDER BY hour, minute"
            ).fetchall()
        else:
            rows = self._connection.execute(
                """
                SELECT * FROM reminders
                WHERE enabled = 1 AND chat_id = ?
                ORDER BY hour, minute
                """,
                (chat_id,),
            ).fetchall()
        return [self._row_to_reminder(row) for row in rows]

    def delete_reminder(self, reminder_id: int, chat_id: int | None = None) -> None:
        """Delete one reminder by id, optionally scoped to one chat."""

        with self._connection:
            if chat_id is None:
                self._connection.execute(
                    "DELETE FROM reminders WHERE id = ?", (reminder_id,)
                )
            else:
                self._connection.execute(
                    "DELETE FROM reminders WHERE id = ? AND chat_id = ?",
                    (reminder_id, chat_id),
                )

    def _find_reminder_id(self, habit_id: int, chat_id: int) -> int:
        """Find the database id for an upserted reminder."""

        row = self._connection.execute(
            "SELECT id FROM reminders WHERE habit_id = ? AND chat_id = ?",
            (habit_id, chat_id),
        ).fetchone()
        if row is None:
            raise ValueError("Reminder was not saved.")
        return int(row["id"])

    @staticmethod
    def _row_to_habit(row: sqlite3.Row) -> Habit:
        """Convert one SQLite row into a Habit object."""

        return Habit(
            id=int(row["id"]),
            name=str(row["name"]),
            description=str(row["description"]),
            periodicity=Periodicity(str(row["periodicity"])),
            target_count=int(row["target_count"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            archived=bool(row["archived"]),
        )

    @staticmethod
    def _row_to_completion(row: sqlite3.Row) -> Completion:
        """Convert one SQLite row into a Completion object."""

        return Completion(
            id=int(row["id"]),
            habit_id=int(row["habit_id"]),
            completed_on=date.fromisoformat(str(row["completed_on"])),
            note=str(row["note"]),
        )

    @staticmethod
    def _row_to_reminder(row: sqlite3.Row) -> Reminder:
        """Convert one SQLite row into a Reminder object."""

        return Reminder(
            id=int(row["id"]),
            habit_id=int(row["habit_id"]),
            chat_id=int(row["chat_id"]),
            hour=int(row["hour"]),
            minute=int(row["minute"]),
            enabled=bool(row["enabled"]),
        )
