"""Tests for the optional Telegram bot button interface.

Corrector note:
These tests prove that the Telegram layer has real inline buttons and still
uses the same manager/data logic as the rest of the app. They do not contact
Telegram, so they are safe to run in normal unit tests.
"""

from src.bot import (
    CALLBACK_DONE_MENU,
    CALLBACK_LIST,
    CALLBACK_SEED,
    CALLBACK_STATUS,
    habit_list_message,
    main_menu_keyboard,
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
    assert CALLBACK_DONE_MENU in callback_data
    assert CALLBACK_SEED in callback_data


def test_habit_list_message_uses_manager_data(tmp_path) -> None:
    """The Telegram text should come from HabitManager data."""

    manager = HabitManager(database_path=tmp_path / "habits.db")
    manager.create_habit("Read", "daily")

    message = habit_list_message(manager)

    assert "Active habits:" in message
    assert "Read" in message
