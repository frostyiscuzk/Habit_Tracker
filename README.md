# Habit Tracker

Beginner-friendly Python habit tracker for the OOFPP portfolio assignment. The app includes object-oriented habit models, SQLite persistence, analytics, a Telegram management bot, a CLI, and a read-only Streamlit analytics dashboard that can be deployed to Railway.

## Corrector Start Here

Open [CORRECTOR_GUIDE.md](CORRECTOR_GUIDE.md). It explains exactly how to install
`requirements.txt`, run tests, message the already-running Telegram bot, test
the Telegram Mini App dashboard, test the CLI, open Streamlit, and find each
assignment requirement.

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
22 passed
```

The tests are grouped by project requirement:

| Test file | What it proves |
| --- | --- |
| `tests/test_habit.py` | OOP models, validation, inheritance behavior, daily/weekly completion rules. |
| `tests/test_storage.py` | SQLite persistence: habits, completions, and reminders are saved and loaded. |
| `tests/test_manager.py` | Composition/service layer: `HabitManager` uses storage and handles reminders. |
| `tests/test_analytics.py` | Functional programming analytics: streak and completion-rate calculations work from input data. |
| `tests/test_bot.py` | Telegram buttons, command parsing, reminders, and Mini App dashboard link. |
| `tests/test_scheduler.py` | APScheduler reminder jobs are created from saved reminder data. |

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
| User interface | `src/dashboard.py`, `app.py` | Streamlit is read-only analytics with Overview, Streaks, and Data tabs. |
| Telegram buttons and management | `src/bot.py` | Telegram bot handles adding, listing, completing, reminders, archiving, deleting, seeding, and opening Streamlit as a Mini App. |
| Reminder scheduler | `src/scheduler.py`, `src/reminder.py` | APScheduler sends daily Telegram reminders saved in SQLite. |
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

Use the same Railway service for Streamlit and Telegram. Add this variable in
Railway if you want the bot to run:

```text
TELEGRAM_BOT_TOKEN=your_token_from_BotFather
```

Railway starts `python -m src.railway`, which starts the Telegram bot and then
starts the read-only Streamlit analytics dashboard.

## Telegram Management Bot

Streamlit is analytics only. Use Telegram for habit changes:

```text
/add Read 10 pages | daily | 1
/add Gym | weekly | 3
/list
/done 1
/archive 1
/delete 1
/remind 1 08:30
/reminders
/deletereminder 1
/seed
```

The bot also has inline buttons for status, listing habits, marking habits done,
showing reminders, showing commands, loading demo data, and opening the
Streamlit analytics dashboard as a Telegram Mini App.
