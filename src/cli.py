"""Command-line interface for the habit tracker.

The CLI is a second interface for the same app logic used by Streamlit. It is
useful for testing the project quickly from the terminal.
"""

from __future__ import annotations

import argparse
from datetime import date

from .analytics import (
    completion_rate,
    current_streak,
    habits_by_periodicity,
    longest_streak_all,
)
from .manager import HabitManager


def build_parser() -> argparse.ArgumentParser:
    """Define all terminal commands and their arguments."""

    parser = argparse.ArgumentParser(description="Track habits from the command line.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("add", help="Create a habit")
    create.add_argument("name")
    create.add_argument("--periodicity", choices=["daily", "weekly"], default="daily")
    create.add_argument("--target", type=int, default=1)
    create.add_argument("--description", default="")

    subparsers.add_parser("list", help="List active habits")

    done = subparsers.add_parser("done", help="Mark a habit complete")
    done.add_argument("habit_id", type=int)
    done.add_argument("--date", dest="completed_on")
    done.add_argument("--note", default="")

    subparsers.add_parser("summary", help="Show dashboard summary")
    subparsers.add_parser("analytics", help="Show habit analytics")
    subparsers.add_parser("seed", help="Replace data with demo habits")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the selected CLI command."""

    parser = build_parser()
    args = parser.parse_args(argv)
    manager = HabitManager()

    if args.command == "add":
        # Create a habit from terminal input.
        habit = manager.create_habit(
            args.name, args.periodicity, args.target, args.description
        )
        print(f"Created #{habit.id}: {habit.name}")
    elif args.command == "list":
        # Print active habits in a compact readable format.
        for habit in manager.list_habits():
            print(f"#{habit.id} {habit.name} ({habit.periodicity.value}, target {habit.target_count})")
    elif args.command == "done":
        # Convert an optional ISO date string into a Python date object.
        completed_on = (
            date.fromisoformat(args.completed_on) if args.completed_on else date.today()
        )
        manager.complete_habit(args.habit_id, completed_on, args.note)
        print(f"Marked habit #{args.habit_id} complete for {completed_on.isoformat()}")
    elif args.command == "summary":
        # Reuse the dashboard summary so CLI and web metrics stay consistent.
        summary = manager.dashboard_summary()
        for key in ("active_habits", "completed_today", "completed_this_week", "total_completions"):
            print(f"{key}: {summary[key]}")
    elif args.command == "analytics":
        # Expose the pure analytics functions from the terminal for marking.
        habits = manager.list_habits()
        completions = manager.list_completions()
        by_periodicity = habits_by_periodicity(habits)
        best_current_streak = max(
            (current_streak(habit, completions) for habit in habits),
            default=0,
        )
        first_completion = min((completion.completed_on for completion in completions), default=date.today())
        rate_rows = [
            f"{habit.name}={completion_rate(habit, completions, first_completion, date.today()):.2f}"
            for habit in habits
        ]
        print(f"current_streak: {best_current_streak}")
        print(f"longest_streak_all: {longest_streak_all(habits, completions)}")
        print(f"completion_rate: {', '.join(rate_rows) if rate_rows else 'none'}")
        print(
            "habits_by_periodicity: "
            f"daily={by_periodicity['daily']}, weekly={by_periodicity['weekly']}"
        )
    elif args.command == "seed":
        # Replace local data with a predictable sample dataset.
        manager.seed_demo_data()
        print("Demo data loaded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
