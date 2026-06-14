"""Optional Telegram bot interface with inline buttons.

Corrector note:
This module shows a second UI for the same habit-tracker logic. The bot uses
Telegram inline keyboard buttons, but the core app still works without running
Telegram because Streamlit and the CLI use the same HabitManager service layer.
"""

from __future__ import annotations

import os
from typing import Final

from .manager import HabitManager

CALLBACK_STATUS: Final = "status"
CALLBACK_LIST: Final = "list"
CALLBACK_DONE_MENU: Final = "done_menu"
CALLBACK_SEED: Final = "seed"
CALLBACK_PREFIX_DONE: Final = "done:"


def status_message(manager: HabitManager | None = None) -> str:
    """Build a short text summary suitable for a Telegram chat message."""

    manager = manager or HabitManager()
    summary = manager.dashboard_summary()
    return (
        "Habit Tracker\n"
        f"Active habits: {summary['active_habits']}\n"
        f"Completed today: {summary['completed_today']}\n"
        f"Completed this week: {summary['completed_this_week']}"
    )


def habit_list_message(manager: HabitManager | None = None) -> str:
    """Return a readable list of active habits for Telegram."""

    manager = manager or HabitManager()
    habits = manager.list_habits()
    if not habits:
        return "No active habits yet. Create habits in the dashboard or CLI."
    lines = ["Active habits:"]
    for habit in habits:
        lines.append(
            f"#{habit.id} {habit.name} ({habit.periodicity.value}, target {habit.target_count})"
        )
    return "\n".join(lines)


def main_menu_keyboard():
    """Build the main Telegram inline keyboard.

    Assignment concept: Telegram buttons. Each button sends callback data that
    the bot handles without the user typing a command.
    """

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Status", callback_data=CALLBACK_STATUS),
                InlineKeyboardButton("List habits", callback_data=CALLBACK_LIST),
            ],
            [
                InlineKeyboardButton("Mark done", callback_data=CALLBACK_DONE_MENU),
                InlineKeyboardButton("Load demo data", callback_data=CALLBACK_SEED),
            ],
        ]
    )


def habit_done_keyboard(manager: HabitManager | None = None):
    """Build one button per active habit so the user can mark it done."""

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    manager = manager or HabitManager()
    rows = [
        [InlineKeyboardButton(habit.name, callback_data=f"{CALLBACK_PREFIX_DONE}{habit.id}")]
        for habit in manager.list_habits()
        if habit.id is not None
    ]
    rows.append([InlineKeyboardButton("Back", callback_data=CALLBACK_STATUS)])
    return InlineKeyboardMarkup(rows)


async def start(update, context) -> None:
    """Handle /start and show the main button menu."""

    await update.message.reply_text(status_message(), reply_markup=main_menu_keyboard())


async def handle_button(update, context) -> None:
    """Handle all Telegram inline button presses."""

    query = update.callback_query
    await query.answer()
    manager = HabitManager()
    data = query.data

    if data == CALLBACK_STATUS:
        await query.edit_message_text(status_message(manager), reply_markup=main_menu_keyboard())
    elif data == CALLBACK_LIST:
        await query.edit_message_text(habit_list_message(manager), reply_markup=main_menu_keyboard())
    elif data == CALLBACK_DONE_MENU:
        await query.edit_message_text("Choose a habit to mark done:", reply_markup=habit_done_keyboard(manager))
    elif data == CALLBACK_SEED:
        manager.seed_demo_data()
        await query.edit_message_text("Demo data loaded.", reply_markup=main_menu_keyboard())
    elif data and data.startswith(CALLBACK_PREFIX_DONE):
        habit_id = int(data.removeprefix(CALLBACK_PREFIX_DONE))
        habit = manager.get_habit(habit_id)
        manager.complete_habit(habit_id)
        await query.edit_message_text(
            f"Marked complete: {habit.name}",
            reply_markup=main_menu_keyboard(),
        )


def build_application(token: str):
    """Create the Telegram application and register command/button handlers."""

    from telegram.ext import Application, CallbackQueryHandler, CommandHandler

    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", start))
    application.add_handler(CallbackQueryHandler(handle_button))
    return application


def main() -> int:
    """Run the Telegram bot when TELEGRAM_BOT_TOKEN is configured."""

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN before starting the Telegram bot.")
    build_application(token).run_polling()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
