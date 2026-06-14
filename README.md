# Habit Tracker

Beginner-friendly Python habit tracker for the OOFPP portfolio assignment. The app includes object-oriented habit models, SQLite persistence, analytics, a CLI, and a Streamlit dashboard that can be deployed to Railway.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Planned Run Command

```bash
streamlit run app.py
```

## First Thing To Check: Tests

The corrector can run the full automated test suite with:

```bash
python -m pytest
```

Expected result:

```text
9 passed
```

The tests are grouped by project requirement:

| Test file | What it proves |
| --- | --- |
| `tests/test_habit.py` | OOP models, validation, inheritance behavior, daily/weekly completion rules. |
| `tests/test_storage.py` | SQLite persistence: habits and completions are saved, loaded, archived, and filtered. |
| `tests/test_manager.py` | Composition/service layer: `HabitManager` uses storage and returns dashboard summaries. |
| `tests/test_analytics.py` | Functional programming analytics: streak and completion-rate calculations work from input data. |
| `tests/test_bot.py` | Telegram inline buttons exist and the bot uses manager data. |

## CLI

```bash
python -m src.cli add "Read 10 pages" --periodicity daily
python -m src.cli list
python -m src.cli done 1
python -m src.cli summary
```

## Assignment Requirements Map

This section shows the corrector exactly where the required programming concepts are implemented.

| Requirement | Where it is implemented | What to look for |
| --- | --- | --- |
| Classes and objects | `src/habit.py` | `Habit`, `DailyHabit`, `WeeklyHabit`, and `Completion` model the main app data. |
| Inheritance | `src/habit.py` | `DailyHabit` and `WeeklyHabit` inherit from the base `Habit` class. |
| Composition | `src/manager.py`, `src/dashboard.py` | `HabitManager` contains and uses a `SQLiteStorage` object. The Streamlit dashboard creates a `HabitManager` instead of handling storage directly. |
| Encapsulation | `src/manager.py`, `src/storage.py` | UI code calls manager methods such as `create_habit()` and `complete_habit()`. SQL details stay inside `SQLiteStorage`. |
| Data persistence | `src/storage.py` | SQLite tables store habits and completion records in `data/habits.db`. |
| Functional programming / pure functions | `src/analytics.py` | Analytics functions receive data as arguments and return calculated results without changing the database. |
| Error handling / validation | `src/habit.py`, `src/manager.py` | Empty habit names, invalid targets, and missing habit ids are checked with clear errors. |
| User interface | `src/dashboard.py`, `app.py` | Streamlit dashboard with tabs for Today, Habits, Analytics, and Data. |
| Telegram buttons | `src/bot.py` | Optional Telegram bot uses inline keyboard buttons for status, habit list, mark done, and demo data. |
| Command-line interface | `src/cli.py` | Terminal commands for adding, listing, completing, summarizing, and seeding habits. |
| Tests | `tests/` | Unit tests cover models, manager behavior, analytics, and SQLite storage. |
| Deployment | `Procfile`, `railway.json`, `app.py` | Railway starts the Streamlit app using the platform `PORT`. |

For an even shorter explanation: composition is mainly in `HabitManager`, because the manager is built from another object, `SQLiteStorage`, and delegates database work to it.

## Railway

Railway can run this project with the included `Procfile` or `railway.json`.

```bash
railway up
```

The app stores data in `data/habits.db` by default. Set `DATABASE_PATH` if you want a different SQLite file path.
