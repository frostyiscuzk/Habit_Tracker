# Corrector Guide

The project is already deployed and running. The corrector does not need to
install or start anything to test the main app.

## Check This First: Live App

Live Streamlit analytics dashboard:

[https://habittrackeriu.up.railway.app/](https://habittrackeriu.up.railway.app/)

Live Telegram bot:

[@Habit_Tracker_IU_bot](https://t.me/Habit_Tracker_IU_bot)

Recommended live test order:

1. Open the Telegram bot and send `/start`.
2. Press the bot buttons: 📊 Status, 📋 List habits, ➕ Add habit, ✅ Mark done,
   🔥 Streaks, ⏰ Reminders, 🔄 Reset demo, 🛠️ Help, 📈 Open analytics dashboard.
3. Press 🔥 Streaks after marking a habit done. This shows current and longest
   streaks directly inside Telegram.
4. Press 📈 Open analytics dashboard inside Telegram. This opens the Streamlit
   dashboard as a Telegram Mini App.
5. Open the Railway dashboard link in a browser and check the same read-only
   analytics tabs.

Important:

- Do not run another copy of the Telegram bot locally. The bot token is already
  configured on the Railway service.
- Running a second bot with the same token can cause Telegram polling conflicts.
- If Telegram still shows old buttons, send `/start` again after Railway
  redeploys.

The rest of this guide is only for optional local tests, CLI checks, or code
review.

## Optional: Run Locally

Use these steps only if you want to run the project on your own machine.

### 1. Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The `requirements.txt` file is commented. It explains why each dependency is
needed.

### 2. Run Tests

```bash
python -m pytest
```

Expected result:

```text
30 passed
```

What the tests cover:

- `tests/test_habit.py`: OOP, inheritance, validation, daily/weekly logic.
- `tests/test_storage.py`: SQLite persistence for habits, completions, reminders.
- `tests/test_manager.py`: composition/service layer, including reminders.
- `tests/test_analytics.py`: pure analytics functions, including streaks.
- `tests/test_bot.py`: Telegram buttons, daily/weekly add flow, compact streak
  display, reminder add/change/delete, reset, and Mini App link.
- `tests/test_scheduler.py`: APScheduler jobs and reminder timezone behavior.

### 3. Test The Already-Running Telegram Bot

The bot is already running on Railway with its token. Message it directly. Do
not start another local bot process.

Try:

```text
/start
/seed
/list
/add Read 10 pages | daily | 1
/done 1
/streaks
/remind 1 08:30
/reminders
/deletereminder 1
/archive 1
```

Also test the buttons:

- 📊 Status
- 📋 List habits
- ✅ Mark done
- 🔥 Streaks
- ⏰ Reminders
- 🛠️ Help
- ➕ Add habit
- 🔄 Reset demo
- 📈 Open analytics dashboard

Add habit behavior:

- Tap ➕ Add habit.
- Pick ☀️ Daily or 🗓️ Weekly.
- Type any habit name, for example `Read 10 pages`.
- The bot creates it with the chosen periodicity.
- Advanced typed command still works if needed:
  `/add Gym | weekly | 3`

Reminder behavior:

- Tap ⏰ Reminders to see saved reminders.
- Tap a habit/time button such as 🌅 Read 08:30 or 🌙 Read 20:00 to add a reminder.
- Tapping a different time for the same habit changes that reminder.
- Tap 🧹 Delete reminder #... to remove a reminder.
- Reminder times use the app timezone, currently Europe/Berlin unless `APP_TIMEZONE`
  is changed on Railway.

The last button opens the Streamlit dashboard as a Telegram Mini App.
Inside the Mini App, the Overview and Streaks tabs both show streak analytics.

### 4. Test The CLI

These commands test the local terminal interface:

```bash
python -m src.cli seed
python -m src.cli list
python -m src.cli add "Read 10 pages" --periodicity daily
python -m src.cli done 1
python -m src.cli summary
```

### 5. Test Streamlit Analytics

This tests the read-only analytics dashboard:

```bash
streamlit run app.py
```

Open:

```text
http://localhost:8501
```

Streamlit is intentionally analytics only. It has no add/edit/delete habit
controls. Habit changes are done through Telegram or CLI.

## Requirement Locations

| Requirement | Where to look |
| --- | --- |
| Requirements file | `requirements.txt` |
| Classes and objects | `src/habit.py` |
| Inheritance | `src/habit.py` |
| Composition | `src/manager.py`, `src/dashboard.py` |
| Encapsulation | `src/manager.py`, `src/storage.py` |
| SQLite persistence | `src/storage.py` |
| Reminder scheduler | `src/reminder.py`, `src/scheduler.py` |
| Pure analytics functions and streak calculations | `src/analytics.py` |
| Streamlit analytics UI | `src/dashboard.py`, `app.py` |
| Telegram bot, streaks, reminders, and Mini App button | `src/bot.py` |
| Railway single-service launcher | `src/railway.py`, `Procfile`, `railway.json` |
| Tests | `tests/` |

More detail is in `docs/assignment_requirements.md`.
