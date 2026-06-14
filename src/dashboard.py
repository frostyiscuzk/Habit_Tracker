"""Streamlit dashboard for the habit tracker.

This file contains the read-only analytics interface. Habit creation,
completion, and management are handled by the Telegram bot and CLI.
"""

from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from .manager import HabitManager


def get_manager() -> HabitManager:
    """Create the service object used by the UI.

    Assignment concept: composition in the UI. The dashboard uses a
    HabitManager object instead of directly creating database queries.
    """

    return HabitManager()


def render_dashboard() -> None:
    """Render the read-only Streamlit analytics app."""

    st.set_page_config(page_title="Habit Analytics", page_icon=":bar_chart:", layout="wide")
    st.title("Habit Analytics")
    st.caption("Read-only dashboard. Add, complete, and manage habits from the Telegram bot.")

    # Load data once at the top so every tab uses the same current state.
    manager = get_manager()
    summary = manager.dashboard_summary()
    habits = manager.list_habits(include_archived=True)

    # Summary metrics give the user a quick overview before the detailed tabs.
    metric_cols = st.columns(4)
    metric_cols[0].metric("Active habits", summary["active_habits"])
    metric_cols[1].metric("Done today", summary["completed_today"])
    metric_cols[2].metric("Done this week", summary["completed_this_week"])
    metric_cols[3].metric("All completions", summary["total_completions"])

    tab_overview, tab_streaks, tab_data = st.tabs(["Overview", "Streaks", "Data"])

    with tab_overview:
        # The Overview tab shows progress trends only. It has no write actions.
        st.subheader("Last 30 days")
        totals = summary["daily_totals"]
        st.bar_chart({day.strftime("%b %d"): total for day, total in totals.items()})

        st.subheader("Active habits")
        active_rows = [
            {
                "habit": habit.name,
                "periodicity": habit.periodicity.value,
                "target": habit.target_count,
                "created": habit.created_at.date().isoformat(),
            }
            for habit in habits
            if not habit.archived
        ]
        if active_rows:
            st.dataframe(active_rows, width="stretch", hide_index=True)
        else:
            st.info("No active habits yet. Create habits with the Telegram bot.")

    with tab_streaks:
        # The Streaks tab shows calculated analytics from src/analytics.py.
        st.subheader("Habit streaks")
        leaderboard = summary["leaderboard"]
        if leaderboard:
            st.dataframe(leaderboard, width="stretch", hide_index=True)
        else:
            st.info("No completion data yet.")

    with tab_data:
        # The Data tab exposes recent records for checking. It is still read-only.
        st.subheader("Recent completions")
        start = date.today() - timedelta(days=30)
        completions = manager.list_completions(start=start)
        habit_names = {habit.id: habit.name for habit in habits}
        rows = [
            {
                "date": completion.completed_on.isoformat(),
                "habit": habit_names.get(completion.habit_id, "Deleted habit"),
                "note": completion.note,
            }
            for completion in completions
        ]
        st.dataframe(rows, width="stretch", hide_index=True)


if __name__ == "__main__":
    render_dashboard()
