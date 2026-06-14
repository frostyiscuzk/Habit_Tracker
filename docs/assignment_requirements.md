# Assignment Requirements Map

This file is written for the corrector. It explains where the main assignment
requirements can be found in the project.

## OOP Classes

Location: `src/habit.py`

- `Habit` is the main class for a trackable habit.
- `Completion` represents one completed habit record.
- `Periodicity` restricts habits to `daily` or `weekly`.

## Inheritance

Location: `src/habit.py`

- `DailyHabit` inherits from `Habit`.
- `WeeklyHabit` inherits from `Habit`.
- Both subclasses reuse the validation and completion-checking behavior from
  the base class.

## Composition

Main location: `src/manager.py`

```python
self.storage = storage or SQLiteStorage(database_path)
```

This is composition because `HabitManager` is built using another object,
`SQLiteStorage`. The manager does not inherit from storage. Instead, it owns and
uses a storage object to save and load habits.

Second location: `src/dashboard.py`

```python
manager = get_manager()
summary = manager.dashboard_summary()
```

The analytics UI is also composed with the manager. The dashboard uses
`HabitManager` to read summaries instead of doing database work directly.

## Encapsulation

Locations: `src/manager.py` and `src/storage.py`

- The bot and CLI call simple methods such as `create_habit()` and
  `complete_habit()`.
- The dashboard calls read-only summary/list methods.
- SQL code is hidden inside `SQLiteStorage`.
- This keeps implementation details away from the UI.

## Persistence

Location: `src/storage.py`

- SQLite stores habits in the `habits` table.
- SQLite stores completed dates in the `completions` table.
- SQLite stores Telegram reminders in the `reminders` table.
- The default database file is `data/habits.db`.

## Functional Programming

Location: `src/analytics.py`

- `current_streak()`
- `longest_streak()`
- `completion_rate()`
- `daily_totals()`
- `habit_leaderboard()`

These functions calculate values from input data and return results. They do
not write to the database or change the UI.

## Streamlit Analytics Interface

Locations: `app.py` and `src/dashboard.py`

- `app.py` is the Streamlit/Railway entrypoint.
- `src/dashboard.py` is read-only analytics.
- It does not create, edit, complete, archive, or delete habits.
- It builds the tabs:
  - Overview
  - Streaks
  - Data

## Telegram Bot With Buttons

Location: `src/bot.py`

The Telegram bot manages habit changes and uses inline keyboard buttons:

- Status
- List habits
- Mark done
- Reminders
- Commands
- Load demo data
- Open analytics dashboard

The important function is:

```python
main_menu_keyboard()
```

It creates `InlineKeyboardButton` objects and returns an
`InlineKeyboardMarkup`. The button callbacks are handled by `handle_button()`.
The dashboard button uses Telegram's `WebAppInfo` to open Streamlit as a Mini
App.

The bot also has text commands for actions that need typed data:

- `/add Read 10 pages | daily | 1`
- `/add Gym | weekly | 3`
- `/list`
- `/done 1`
- `/remind 1 08:30`
- `/reminders`
- `/deletereminder 1`
- `/archive 1`
- `/delete 1`
- `/seed`

## CLI

Location: `src/cli.py`

The command-line interface supports:

- `add`
- `list`
- `done`
- `summary`
- `seed`

## Tests

Location: `tests/`

- `test_habit.py` checks model validation and habit completion logic.
- `test_storage.py` checks SQLite saving and loading, including reminders.
- `test_manager.py` checks the app service layer, including reminders.
- `test_analytics.py` checks streak and completion-rate calculations.
- `test_bot.py` checks that Telegram inline buttons, command parsing, and the
  reminder commands, and the Mini App dashboard link are present.
- `test_scheduler.py` checks that reminder records become APScheduler jobs.

## Deployment

Locations: `Procfile`, `railway.json`, and `app.py`

Railway runs one service. `src/railway.py` starts the Telegram bot first, then
starts Streamlit.

Railway start command:

```bash
python -m src.railway
```

The Telegram token is configured in the same Railway service:

```text
TELEGRAM_BOT_TOKEN=your_token_from_BotFather
```
