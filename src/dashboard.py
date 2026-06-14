"""Streamlit dashboard for the habit tracker.

This file contains the web user interface. It uses Streamlit widgets to create,
edit, complete, and analyze habits.
"""

from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from .habit import Periodicity
from .manager import HabitManager


def get_manager() -> HabitManager:
    """Create the service object used by the UI.

    Assignment concept: composition in the UI. The dashboard uses a
    HabitManager object instead of directly creating database queries.
    """

    return HabitManager()


def render_dashboard() -> None:
    """Render the complete Streamlit app."""

    st.set_page_config(page_title="Habit Tracker", page_icon=":white_check_mark:", layout="wide")
    st.title("Habit Tracker")

    # Load data once at the top so every tab uses the same current state.
    manager = get_manager()
    summary = manager.dashboard_summary()
    habits = manager.list_habits(include_archived=True)
    active_habits = [habit for habit in habits if not habit.archived]

    # Summary metrics give the user a quick overview before the detailed tabs.
    metric_cols = st.columns(4)
    metric_cols[0].metric("Active habits", summary["active_habits"])
    metric_cols[1].metric("Done today", summary["completed_today"])
    metric_cols[2].metric("Done this week", summary["completed_this_week"])
    metric_cols[3].metric("All completions", summary["total_completions"])

    tab_today, tab_habits, tab_analytics, tab_data = st.tabs(
        ["Today", "Habits", "Analytics", "Data"]
    )

    with tab_today:
        # The Today tab is for fast daily use: choose a date and mark done.
        st.subheader("Log progress")
        if not active_habits:
            st.info("Create a habit to start tracking.")
        for habit in active_habits:
            with st.container(border=True):
                cols = st.columns([3, 1, 1])
                cols[0].markdown(f"**{habit.name}**")
                cols[0].caption(
                    f"{habit.periodicity.value.title()} target: {habit.target_count}"
                )
                selected_day = cols[1].date_input(
                    "Date",
                    value=date.today(),
                    key=f"date-{habit.id}",
                    label_visibility="collapsed",
                )
                if cols[2].button("Mark done", key=f"complete-{habit.id}", width="stretch"):
                    manager.complete_habit(habit.id or 0, selected_day)
                    st.rerun()

    with tab_habits:
        # The Habits tab handles creating and editing habit definitions.
        st.subheader("Create a habit")
        with st.form("new-habit", clear_on_submit=True):
            name = st.text_input("Name", placeholder="Read 10 pages")
            description = st.text_area("Description", placeholder="Optional notes")
            cols = st.columns(2)
            periodicity = cols[0].selectbox(
                "Periodicity", [Periodicity.DAILY.value, Periodicity.WEEKLY.value]
            )
            target_count = cols[1].number_input("Target count", min_value=1, value=1, step=1)
            submitted = st.form_submit_button("Create habit")
            if submitted:
                manager.create_habit(name, periodicity, int(target_count), description)
                st.rerun()

        st.subheader("Manage habits")
        include_archived = st.checkbox("Show archived habits")
        for habit in manager.list_habits(include_archived=include_archived):
            with st.expander(habit.name, expanded=False):
                with st.form(f"edit-{habit.id}"):
                    edit_name = st.text_input("Name", value=habit.name)
                    edit_description = st.text_area("Description", value=habit.description)
                    cols = st.columns(3)
                    edit_periodicity = cols[0].selectbox(
                        "Periodicity",
                        [Periodicity.DAILY.value, Periodicity.WEEKLY.value],
                        index=0 if habit.periodicity == Periodicity.DAILY else 1,
                    )
                    edit_target = cols[1].number_input(
                        "Target count",
                        min_value=1,
                        value=habit.target_count,
                        step=1,
                    )
                    edit_archived = cols[2].checkbox("Archived", value=habit.archived)
                    saved = st.form_submit_button("Save changes")
                    if saved:
                        manager.update_habit(
                            habit.id or 0,
                            edit_name,
                            edit_periodicity,
                            int(edit_target),
                            edit_description,
                            edit_archived,
                        )
                        st.rerun()

    with tab_analytics:
        # The Analytics tab shows progress trends and streak information.
        st.subheader("Last 30 days")
        totals = summary["daily_totals"]
        st.bar_chart({day.strftime("%b %d"): total for day, total in totals.items()})

        st.subheader("Habit streaks")
        leaderboard = summary["leaderboard"]
        if leaderboard:
            st.dataframe(leaderboard, width="stretch", hide_index=True)
        else:
            st.info("No completion data yet.")

    with tab_data:
        # The Data tab exposes the raw recent completion records for checking.
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
        if st.button("Load demo data"):
            manager.seed_demo_data()
            st.rerun()


if __name__ == "__main__":
    render_dashboard()
