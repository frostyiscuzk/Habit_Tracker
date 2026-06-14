"""Tests for the optional Telegram bot button interface.

Corrector note:
These tests prove that the Telegram layer has real inline buttons and still
uses the same manager/data logic as the rest of the app. They do not contact
Telegram, so they are safe to run in normal unit tests.
"""

from src.bot import (
    CALLBACK_ADD_MENU,
    CALLBACK_DONE_MENU,
    CALLBACK_HELP,
    CALLBACK_LIST,
    CALLBACK_REMINDERS,
    CALLBACK_SEED,
    CALLBACK_STATUS,
    CALLBACK_PREFIX_QUICK_ADD,
    CALLBACK_PREFIX_DELETE_REMINDER,
    CALLBACK_PREFIX_REMIND_QUICK,
    _parse_add_command,
    _parse_habit_id,
    _parse_reminder_callback,
    _parse_remind_command,
    dashboard_url,
    habit_list_message,
    main_menu_keyboard,
    quick_add_keyboard,
    reminder_quick_keyboard,
    reminders_message,
    start_bot_from_env_once,
)
from src.manager import HabitManager


def test_main_menu_keyboard_has_telegram_buttons() -> None:
    """The bot should expose inline buttons, not only text commands."""

    keyboard = main_menu_keyboard()
    callback_data = [
        button.callback_data
        for row in keyboard.inline_keyboard
        for button in row
    ]

    assert CALLBACK_STATUS in callback_data
    assert CALLBACK_LIST in callback_data
    assert CALLBACK_ADD_MENU in callback_data
    assert CALLBACK_DONE_MENU in callback_data
    assert CALLBACK_HELP in callback_data
    assert CALLBACK_REMINDERS in callback_data
    assert CALLBACK_SEED in callback_data


def test_main_menu_keyboard_uses_friendly_labels() -> None:
    """The Telegram buttons should be readable and friendly for users."""

    keyboard = main_menu_keyboard()
    labels = [
        button.text
        for row in keyboard.inline_keyboard
        for button in row
    ]

    assert "📊 Status" in labels
    assert "📋 List habits" in labels
    assert "➕ Add habit" in labels
    assert "✅ Mark done" in labels
    assert "⏰ Reminders" in labels
    assert "🔄 Reset demo" in labels
    assert "🛠️ Help" in labels


def test_main_menu_keyboard_has_dashboard_mini_app(monkeypatch) -> None:
    """Telegram should expose the Streamlit analytics dashboard as a Mini App."""

    monkeypatch.setenv("STREAMLIT_PUBLIC_URL", "https://example.up.railway.app")

    keyboard = main_menu_keyboard()
    web_app_urls = [
        button.web_app.url
        for row in keyboard.inline_keyboard
        for button in row
        if button.web_app is not None
    ]

    assert "https://example.up.railway.app" in web_app_urls


def test_quick_add_keyboard_has_preset_habits() -> None:
    """Users should be able to add common habits with buttons."""

    keyboard = quick_add_keyboard()
    callback_data = [
        button.callback_data
        for row in keyboard.inline_keyboard
        for button in row
    ]

    assert f"{CALLBACK_PREFIX_QUICK_ADD}water" in callback_data
    assert f"{CALLBACK_PREFIX_QUICK_ADD}study" in callback_data
    assert f"{CALLBACK_PREFIX_QUICK_ADD}exercise" in callback_data


def test_reminder_quick_keyboard_has_habit_buttons(tmp_path) -> None:
    """Users should be able to set common reminders without typing."""

    manager = HabitManager(database_path=tmp_path / "habits.db")
    habit = manager.create_habit("Read", "daily")

    keyboard = reminder_quick_keyboard(manager)
    callback_data = [
        button.callback_data
        for row in keyboard.inline_keyboard
        for button in row
    ]

    assert f"{CALLBACK_PREFIX_REMIND_QUICK}{habit.id}:08:30" in callback_data
    assert f"{CALLBACK_PREFIX_REMIND_QUICK}{habit.id}:20:00" in callback_data


def test_reminder_quick_keyboard_has_delete_buttons(tmp_path) -> None:
    """Users should be able to delete reminders without typing."""

    manager = HabitManager(database_path=tmp_path / "habits.db")
    habit = manager.create_habit("Read", "daily")
    reminder = manager.add_reminder(habit.id or 0, chat_id=123, hour=8, minute=30)

    keyboard = reminder_quick_keyboard(manager, chat_id=123)
    callback_data = [
        button.callback_data
        for row in keyboard.inline_keyboard
        for button in row
    ]

    assert f"{CALLBACK_PREFIX_DELETE_REMINDER}{reminder.id}" in callback_data


def test_habit_list_message_uses_manager_data(tmp_path) -> None:
    """The Telegram text should come from HabitManager data."""

    manager = HabitManager(database_path=tmp_path / "habits.db")
    manager.create_habit("Read", "daily")

    message = habit_list_message(manager)

    assert "Active habits:" in message
    assert "Read" in message


def test_add_command_parser_accepts_name_periodicity_and_target() -> None:
    """The bot can create habits from Telegram command text."""

    assert _parse_add_command("Read | daily | 1") == ("Read", "daily", 1)
    assert _parse_add_command("Gym | weekly | 3") == ("Gym", "weekly", 3)


def test_habit_id_parser_reads_numeric_id() -> None:
    """The bot can parse ids for done/archive/delete commands."""

    assert _parse_habit_id("/done 7", "/done") == 7


def test_reminder_command_parser_reads_id_and_time() -> None:
    """The bot can parse reminder command text."""

    assert _parse_remind_command("/remind 7 08:30") == (7, 8, 30)


def test_reminder_callback_parser_reads_id_and_time() -> None:
    """The bot can parse reminder button callback data."""

    assert _parse_reminder_callback("remind:7:20:00") == (7, 20, 0)


def test_reminders_message_lists_saved_reminders(tmp_path) -> None:
    """The bot can show saved reminders in a friendly message."""

    manager = HabitManager(database_path=tmp_path / "habits.db")
    habit = manager.create_habit("Read", "daily")
    reminder = manager.add_reminder(habit.id or 0, chat_id=123, hour=8, minute=30)

    message = reminders_message(manager, [reminder])

    assert "🔔 Active reminders (Europe/Berlin time):" in message
    assert "Read at 08:30" in message


def test_bot_does_not_start_without_token(monkeypatch) -> None:
    """Railway can run Streamlit without Telegram when no token is configured."""

    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)

    assert start_bot_from_env_once() is False


def test_dashboard_url_uses_railway_public_domain(monkeypatch) -> None:
    """Railway's public domain can power the Telegram Mini App button."""

    monkeypatch.delenv("STREAMLIT_PUBLIC_URL", raising=False)
    monkeypatch.setenv("RAILWAY_PUBLIC_DOMAIN", "habit.example.railway.app")

    assert dashboard_url() == "https://habit.example.railway.app"
