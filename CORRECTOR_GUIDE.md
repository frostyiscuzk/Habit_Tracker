# Corrector Guide

This is the shortest path to test the project.

## 1. Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The `requirements.txt` file is commented. It explains why each dependency is
needed.

## 2. Run Tests

```bash
python -m pytest
```

Expected result:

```text
16 passed
```

What the tests cover:

- `tests/test_habit.py`: OOP, inheritance, validation, daily/weekly logic.
- `tests/test_storage.py`: SQLite persistence.
- `tests/test_manager.py`: composition/service layer.
- `tests/test_analytics.py`: pure analytics functions.
- `tests/test_bot.py`: Telegram buttons, commands, and Mini App dashboard link.

## 3. Test The Already-Running Telegram Bot

The bot is already running. Message it directly.

Try:

```text
/start
/seed
/list
/add Read 10 pages | daily | 1
/done 1
/archive 1
```

Also test the buttons:

- Status
- List habits
- Mark done
- Commands
- Load demo data
- Open analytics dashboard

The last button opens the Streamlit dashboard as a Telegram Mini App.

## 4. Test The CLI

```bash
python -m src.cli seed
python -m src.cli list
python -m src.cli add "Read 10 pages" --periodicity daily
python -m src.cli done 1
python -m src.cli summary
```

## 5. Test Streamlit Analytics

```bash
streamlit run app.py
```

Open:

```text
http://localhost:8501
```

Streamlit is intentionally analytics only. It has no add/edit/delete habit
controls. Habit changes are done through Telegram or CLI.

## 6. Requirement Locations

| Requirement | Where to look |
| --- | --- |
| Requirements file | `requirements.txt` |
| Classes and objects | `src/habit.py` |
| Inheritance | `src/habit.py` |
| Composition | `src/manager.py`, `src/dashboard.py` |
| Encapsulation | `src/manager.py`, `src/storage.py` |
| SQLite persistence | `src/storage.py` |
| Pure analytics functions | `src/analytics.py` |
| Streamlit analytics UI | `src/dashboard.py`, `app.py` |
| Telegram bot and Mini App button | `src/bot.py` |
| Railway single-service launcher | `src/railway.py`, `Procfile`, `railway.json` |
| Tests | `tests/` |

More detail is in `docs/assignment_requirements.md`.
