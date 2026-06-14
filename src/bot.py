"""Optional Telegram bot interface with inline buttons.

Corrector note:
This module shows a second UI for the same habit-tracker logic. The bot uses
Telegram inline keyboard buttons, but the core app still works without running
Telegram because Streamlit and the CLI use the same HabitManager service layer.
The Streamlit app is read-only analytics; this bot handles habit changes.
"""

from __future__ import annotations

import asyncio
import os
import threading
from typing import Final

from .manager import HabitManager

CALLBACK_STATUS: Final = "status"
CALLBACK_LIST: Final = "list"
CALLBACK_DONE_MENU: Final = "done_menu"
CALLBACK_HELP: Final = "help"
CALLBACK_SEED: Final = "seed"
CALLBACK_PREFIX_DONE: Final = "done:"

_bot_lock = threading.Lock()
_bot_thread: threading.Thread | None = None


def status_message(manager: HabitManager | None = None) -> str:
    """Build a short text summary suitable for a Telegram chat message."""

    manager = manager or HabitManager()
    summary = manager.dashboard_summary()
    return (
        "🌱 Habit Tracker\n\n"
        f"📌 Active habits: {summary['active_habits']}\n"
        f"✅ Completed today: {summary['completed_today']}\n"
        f"📅 Completed this week: {summary['completed_this_week']}\n\n"
        "Use the buttons below, or type /help."
    )


def habit_list_message(manager: HabitManager | None = None) -> str:
    """Return a readable list of active habits for Telegram."""

    manager = manager or HabitManager()
    habits = manager.list_habits()
    if not habits:
        return "📝 No active habits yet.\n\nCreate one with:\n/add Read 10 pages | daily | 1"
    lines = ["📋 Active habits:"]
    for habit in habits:
        cadence_icon = "☀️" if habit.periodicity.value == "daily" else "🗓️"
        lines.append(
            f"{cadence_icon} #{habit.id} {habit.name} "
            f"({habit.periodicity.value}, target {habit.target_count})"
        )
    return "\n".join(lines)


def help_message() -> str:
    """Explain Telegram commands that manage habits."""

    return "\n".join(
        [
            "🛠️ Manage habits from Telegram",
            "",
            "➕ Add daily habit:",
            "/add Read 10 pages | daily | 1",
            "",
            "➕ Add weekly habit:",
            "/add Gym | weekly | 3",
            "",
            "📋 List habits: /list",
            "✅ Mark done: /done 1",
            "📦 Archive: /archive 1",
            "🗑️ Delete: /delete 1",
            "🌱 Demo data: /seed",
            "",
            "📊 Streamlit is only for analytics.",
        ]
    )


def dashboard_url() -> str | None:
    """Return the public Streamlit URL for the Telegram Mini App button."""

    explicit_url = os.getenv("STREAMLIT_PUBLIC_URL")
    if explicit_url:
        return explicit_url
    railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
    if railway_domain:
        return f"https://{railway_domain}"
    return None


def main_menu_keyboard():
    """Build the main Telegram inline keyboard.

    Assignment concept: Telegram buttons. Each button sends callback data that
    the bot handles without the user typing a command.
    """

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

    rows = [
        [
            InlineKeyboardButton("📊 Status", callback_data=CALLBACK_STATUS),
            InlineKeyboardButton("📋 List habits", callback_data=CALLBACK_LIST),
        ],
        [
            InlineKeyboardButton("✅ Mark done", callback_data=CALLBACK_DONE_MENU),
            InlineKeyboardButton("🛠️ Commands", callback_data=CALLBACK_HELP),
        ],
        [
            InlineKeyboardButton("🌱 Load demo data", callback_data=CALLBACK_SEED),
        ],
    ]
    mini_app_url = dashboard_url()
    if mini_app_url:
        rows.append(
            [
                InlineKeyboardButton(
                    "📈 Open analytics dashboard",
                    web_app=WebAppInfo(url=mini_app_url),
                )
            ]
        )

    return InlineKeyboardMarkup(rows)


def habit_done_keyboard(manager: HabitManager | None = None):
    """Build one button per active habit so the user can mark it done."""

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    manager = manager or HabitManager()
    rows = [
        [InlineKeyboardButton(f"✅ {habit.name}", callback_data=f"{CALLBACK_PREFIX_DONE}{habit.id}")]
        for habit in manager.list_habits()
        if habit.id is not None
    ]
    rows.append([InlineKeyboardButton("⬅️ Back", callback_data=CALLBACK_STATUS)])
    return InlineKeyboardMarkup(rows)


async def start(update, context) -> None:
    """Handle /start and show the main button menu."""

    await update.message.reply_text(
        f"👋 Welcome!\n\n{status_message()}\n\n{help_message()}",
        reply_markup=main_menu_keyboard(),
    )


async def list_habits(update, context) -> None:
    """Handle /list and show active habits."""

    await update.message.reply_text(habit_list_message(), reply_markup=main_menu_keyboard())


async def add_habit(update, context) -> None:
    """Handle /add Name | daily_or_weekly | target_count."""

    text = update.message.text.removeprefix("/add").strip()
    try:
        name, periodicity, target_count = _parse_add_command(text)
        habit = HabitManager().create_habit(name, periodicity, target_count)
    except ValueError as exc:
        await update.message.reply_text(str(exc), reply_markup=main_menu_keyboard())
        return

    await update.message.reply_text(
        f"✨ Created habit #{habit.id}: {habit.name}",
        reply_markup=main_menu_keyboard(),
    )


async def done_habit(update, context) -> None:
    """Handle /done habit_id."""

    try:
        habit_id = _parse_habit_id(update.message.text, "/done")
        manager = HabitManager()
        habit = manager.get_habit(habit_id)
        manager.complete_habit(habit_id)
    except ValueError as exc:
        await update.message.reply_text(str(exc), reply_markup=main_menu_keyboard())
        return

    await update.message.reply_text(f"✅ Marked complete: {habit.name}", reply_markup=main_menu_keyboard())


async def archive_habit(update, context) -> None:
    """Handle /archive habit_id."""

    try:
        habit_id = _parse_habit_id(update.message.text, "/archive")
        habit = HabitManager().archive_habit(habit_id)
    except ValueError as exc:
        await update.message.reply_text(str(exc), reply_markup=main_menu_keyboard())
        return

    await update.message.reply_text(f"📦 Archived habit: {habit.name}", reply_markup=main_menu_keyboard())


async def delete_habit(update, context) -> None:
    """Handle /delete habit_id."""

    try:
        habit_id = _parse_habit_id(update.message.text, "/delete")
        manager = HabitManager()
        habit = manager.get_habit(habit_id)
        manager.delete_habit(habit_id)
    except ValueError as exc:
        await update.message.reply_text(str(exc), reply_markup=main_menu_keyboard())
        return

    await update.message.reply_text(f"🗑️ Deleted habit: {habit.name}", reply_markup=main_menu_keyboard())


async def seed_data(update, context) -> None:
    """Handle /seed and load demo data."""

    HabitManager().seed_demo_data()
    await update.message.reply_text("🌱 Demo data loaded.", reply_markup=main_menu_keyboard())


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
    elif data == CALLBACK_HELP:
        await query.edit_message_text(help_message(), reply_markup=main_menu_keyboard())
    elif data == CALLBACK_DONE_MENU:
        await query.edit_message_text("✅ Choose a habit to mark done:", reply_markup=habit_done_keyboard(manager))
    elif data == CALLBACK_SEED:
        manager.seed_demo_data()
        await query.edit_message_text("🌱 Demo data loaded.", reply_markup=main_menu_keyboard())
    elif data and data.startswith(CALLBACK_PREFIX_DONE):
        habit_id = int(data.removeprefix(CALLBACK_PREFIX_DONE))
        habit = manager.get_habit(habit_id)
        manager.complete_habit(habit_id)
        await query.edit_message_text(
            f"✅ Marked complete: {habit.name}",
            reply_markup=main_menu_keyboard(),
        )


def build_application(token: str):
    """Create the Telegram application and register command/button handlers."""

    from telegram.ext import Application, CallbackQueryHandler, CommandHandler

    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(CommandHandler("list", list_habits))
    application.add_handler(CommandHandler("add", add_habit))
    application.add_handler(CommandHandler("done", done_habit))
    application.add_handler(CommandHandler("archive", archive_habit))
    application.add_handler(CommandHandler("delete", delete_habit))
    application.add_handler(CommandHandler("seed", seed_data))
    application.add_handler(CallbackQueryHandler(handle_button))
    return application


def start_bot_from_env_once() -> bool:
    """Start Telegram polling in the current Railway web service.

    If TELEGRAM_BOT_TOKEN is not set, nothing happens and Streamlit still runs.
    If the token is set, the bot starts once in a background thread. This lets
    one Railway service run both the analytics dashboard and Telegram bot.
    """

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return False

    global _bot_thread
    with _bot_lock:
        if _bot_thread is not None and _bot_thread.is_alive():
            return True
        _bot_thread = threading.Thread(
            target=_run_polling_worker,
            args=(token,),
            daemon=True,
            name="telegram-bot-polling",
        )
        _bot_thread.start()
        return True


def _run_polling_worker(token: str) -> None:
    """Run Telegram polling without installing OS signal handlers."""

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        build_application(token).run_polling(
            close_loop=True,
            drop_pending_updates=True,
            stop_signals=None,
        )
    except Exception as exc:
        print(f"Telegram bot stopped: {exc}", flush=True)


def _parse_add_command(text: str) -> tuple[str, str, int]:
    """Parse the /add command body and return validated values."""

    parts = [part.strip() for part in text.split("|")]
    if len(parts) != 3:
        raise ValueError("Use: /add Habit name | daily | 1")
    name, periodicity, target_text = parts
    if periodicity not in {"daily", "weekly"}:
        raise ValueError("Periodicity must be daily or weekly.")
    try:
        target_count = int(target_text)
    except ValueError as exc:
        raise ValueError("Target count must be a number.") from exc
    if target_count < 1:
        raise ValueError("Target count must be at least 1.")
    return name, periodicity, target_count


def _parse_habit_id(text: str, command: str) -> int:
    """Parse a command like /done 3 and return the habit id."""

    value = text.removeprefix(command).strip()
    if not value:
        raise ValueError(f"Use: {command} habit_id")
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError("Habit id must be a number.") from exc


def main() -> int:
    """Run the Telegram bot when TELEGRAM_BOT_TOKEN is configured."""

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN before starting the Telegram bot.")
    build_application(token).run_polling()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
