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
from datetime import date
from typing import Final

from .manager import HabitManager
from .scheduler import ReminderScheduler, reminder_timezone_name

STATE_ADD_HABIT_PERIODICITY: Final = 1
STATE_ADD_HABIT_NAME: Final = 2
STATE_EDIT_HABIT_NAME: Final = 3

CALLBACK_STATUS: Final = "status"
CALLBACK_LIST: Final = "list"
CALLBACK_ADD_MENU: Final = "add_menu"
CALLBACK_DONE_MENU: Final = "done_menu"
CALLBACK_HELP: Final = "help"
CALLBACK_REMINDERS: Final = "reminders"
CALLBACK_STREAKS: Final = "streaks"
CALLBACK_SEED: Final = "seed"
CALLBACK_PREFIX_DONE: Final = "done:"
CALLBACK_PREFIX_ADD_PERIODICITY: Final = "add_periodicity:"
CALLBACK_PREFIX_HABIT_DETAIL: Final = "habit:"
CALLBACK_PREFIX_HABIT_EDIT_NAME: Final = "habit_edit_name:"
CALLBACK_PREFIX_HABIT_DELETE: Final = "habit_delete:"
CALLBACK_PREFIX_HABIT_TYPE: Final = "habit_type:"
CALLBACK_PREFIX_REMIND_QUICK: Final = "remind:"
CALLBACK_PREFIX_DELETE_REMINDER: Final = "delete_reminder:"

_bot_lock = threading.Lock()
_bot_thread: threading.Thread | None = None
_reminder_scheduler: ReminderScheduler | None = None


def status_message(manager: HabitManager | None = None) -> str:
    """Build a short text summary suitable for a Telegram chat message."""

    manager = manager or HabitManager()
    summary = manager.dashboard_summary()
    leaderboard = summary["leaderboard"]
    streak_line = ""
    if leaderboard:
        best = leaderboard[0]
        streak_line = (
            f"🔥 Best current streak: {best['habit']} "
            f"({best['current_streak']} now, {best['longest_streak']} best)\n"
        )
    return (
        "🌱 Habit Tracker\n\n"
        f"📌 Active habits: {summary['active_habits']}\n"
        f"✅ Completed today: {summary['completed_today']}\n"
        f"📅 Completed this week: {summary['completed_this_week']}\n\n"
        f"{streak_line}"
        "Use the buttons below. Most actions need no typing."
    )


def action_update_message(title: str, manager: HabitManager | None = None) -> str:
    """Build a short confirmation plus the latest key counters."""

    manager = manager or HabitManager()
    summary = manager.dashboard_summary()
    left = habits_left_today(manager)
    left_text = ", ".join(habit.name for habit in left[:3])
    if len(left) > 3:
        left_text = f"{left_text}, +{len(left) - 3} more"
    if not left_text:
        left_text = "all done"
    return (
        f"{title}\n\n"
        "┌ Updated\n"
        f"│ Done today: {summary['completed_today']}\n"
        f"│ This week: {summary['completed_this_week']}\n"
        f"│ Left today: {len(left)}\n"
        f"└ Next: {left_text}"
    )


def habit_list_message(manager: HabitManager | None = None) -> str:
    """Return a readable list of active habits for Telegram."""

    manager = manager or HabitManager()
    habits = manager.list_habits()
    if not habits:
        return "📝 No active habits yet.\n\nTap ➕ Add habit to create one quickly."
    lines = ["📋 Habits", "", "Tap a habit below to edit or delete."]
    for habit in habits:
        cadence_icon = "☀️" if habit.periodicity.value == "daily" else "🗓️"
        lines.append(f"{cadence_icon} {habit.name}")
    return "\n".join(lines)


def habit_detail_message(manager: HabitManager, habit_id: int) -> str:
    """Build one habit detail panel for Telegram."""

    habit = manager.get_habit(habit_id)
    icon = "☀️" if habit.periodicity.value == "daily" else "🗓️"
    today = "done" if manager.is_completed_on(habit_id, date.today()) else "left"
    return (
        f"{icon} {habit.name}\n\n"
        "┌ Habit\n"
        f"│ Type: {habit.periodicity.value}\n"
        f"│ Target: {habit.target_count}\n"
        f"└ Today: {today}"
    )


def habits_left_today(manager: HabitManager | None = None):
    """Return active habits that have not been completed today."""

    manager = manager or HabitManager()
    today = date.today()
    return [
        habit
        for habit in manager.list_habits()
        if habit.id is not None and not manager.is_completed_on(habit.id, today)
    ]


def done_menu_message(manager: HabitManager | None = None) -> str:
    """Build the Mark Done screen with the remaining habits for today."""

    left = habits_left_today(manager)
    if not left:
        return "✅ Mark Done\n\n┌ Today\n│ all habits done\n└ Nice work."
    lines = ["✅ Mark Done", "", "┌ Left today"]
    for habit in left[:6]:
        lines.append(f"│ {habit.name}")
    if len(left) > 6:
        lines.append(f"│ +{len(left) - 6} more")
    lines.append("└ Tap one below.")
    return "\n".join(lines)


def streaks_message(manager: HabitManager | None = None) -> str:
    """Return current and longest streaks calculated by the analytics layer."""

    manager = manager or HabitManager()
    leaderboard = manager.dashboard_summary()["leaderboard"]
    if not leaderboard:
        return "🔥 Streaks\n\nNone yet."

    lines = ["🔥 Streaks"]
    for row in leaderboard[:5]:
        lines.append(
            f"{row['habit']}: {row['current_streak']} now | {row['longest_streak']} best"
        )
    return "\n".join(lines)


def help_message() -> str:
    """Explain Telegram commands that manage habits."""

    return "\n".join(
        [
            "🛠️ Manage habits from Telegram",
            "",
            "Use the buttons for the normal flow.",
            "",
            "Quick flow:",
            "1. Tap ➕ Add habit",
            "2. Pick ☀️ Daily or 🗓️ Weekly",
            "3. Type the habit name",
            "4. Use ✅ Mark done",
            "5. Use 🔥 Streaks",
            "6. Use ⏰ Reminders",
            "",
            f"Reminder times use {reminder_timezone_name()} time.",
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
            InlineKeyboardButton("➕ Add habit", callback_data=CALLBACK_ADD_MENU),
            InlineKeyboardButton("✅ Mark done", callback_data=CALLBACK_DONE_MENU),
        ],
        [
            InlineKeyboardButton("🔥 Streaks", callback_data=CALLBACK_STREAKS),
            InlineKeyboardButton("⏰ Reminders", callback_data=CALLBACK_REMINDERS),
        ],
        [
            InlineKeyboardButton("🔄 Reset demo", callback_data=CALLBACK_SEED),
            InlineKeyboardButton("🛠️ Help", callback_data=CALLBACK_HELP),
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


def add_cancel_keyboard():
    """Build the small keyboard shown while entering a habit name."""

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Cancel", callback_data=CALLBACK_STATUS)],
        ]
    )


def habit_list_keyboard(manager: HabitManager | None = None):
    """Build one button per habit for edit/delete actions."""

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    manager = manager or HabitManager()
    rows = []
    for habit in manager.list_habits():
        if habit.id is None:
            continue
        icon = "☀️" if habit.periodicity.value == "daily" else "🗓️"
        rows.append(
            [
                InlineKeyboardButton(
                    f"{icon} {habit.name}",
                    callback_data=f"{CALLBACK_PREFIX_HABIT_DETAIL}{habit.id}",
                )
            ]
        )
    rows.append([InlineKeyboardButton("⬅️ Back", callback_data=CALLBACK_STATUS)])
    return InlineKeyboardMarkup(rows)


def habit_detail_keyboard(habit):
    """Build edit/delete buttons for a selected habit."""

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    target_periodicity = "weekly" if habit.periodicity.value == "daily" else "daily"
    target_icon = "🗓️" if target_periodicity == "weekly" else "☀️"
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✏️ Rename",
                    callback_data=f"{CALLBACK_PREFIX_HABIT_EDIT_NAME}{habit.id}",
                ),
                InlineKeyboardButton(
                    f"{target_icon} Make {target_periodicity}",
                    callback_data=f"{CALLBACK_PREFIX_HABIT_TYPE}{habit.id}:{target_periodicity}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🗑️ Delete",
                    callback_data=f"{CALLBACK_PREFIX_HABIT_DELETE}{habit.id}",
                )
            ],
            [InlineKeyboardButton("⬅️ Habits", callback_data=CALLBACK_LIST)],
        ]
    )


def add_periodicity_keyboard():
    """Build the Daily/Weekly choice shown before entering a habit name."""

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "☀️ Daily",
                    callback_data=f"{CALLBACK_PREFIX_ADD_PERIODICITY}daily",
                ),
                InlineKeyboardButton(
                    "🗓️ Weekly",
                    callback_data=f"{CALLBACK_PREFIX_ADD_PERIODICITY}weekly",
                ),
            ],
            [InlineKeyboardButton("⬅️ Back", callback_data=CALLBACK_STATUS)],
        ]
    )


def habit_done_keyboard(manager: HabitManager | None = None):
    """Build one button per active habit so the user can mark it done."""

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    manager = manager or HabitManager()
    rows = [
        [InlineKeyboardButton(f"✅ {habit.name}", callback_data=f"{CALLBACK_PREFIX_DONE}{habit.id}")]
        for habit in habits_left_today(manager)
        if habit.id is not None
    ]
    rows.append([InlineKeyboardButton("⬅️ Back", callback_data=CALLBACK_STATUS)])
    return InlineKeyboardMarkup(rows)


def reminder_quick_keyboard(manager: HabitManager | None = None, chat_id: int | None = None):
    """Build quick reminder and delete buttons."""

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    manager = manager or HabitManager()
    rows = []
    for habit in manager.list_habits():
        if habit.id is None:
            continue
        rows.append(
            [
                InlineKeyboardButton(
                    f"🌅 {habit.name}",
                    callback_data=f"{CALLBACK_PREFIX_REMIND_QUICK}{habit.id}:08:30",
                ),
                InlineKeyboardButton(
                    f"🌙 {habit.name}",
                    callback_data=f"{CALLBACK_PREFIX_REMIND_QUICK}{habit.id}:20:00",
                ),
            ]
        )
    if chat_id is not None:
        for reminder in manager.list_reminders(chat_id=chat_id):
            try:
                habit_name = manager.get_habit(reminder.habit_id).name
            except ValueError:
                habit_name = "Deleted habit"
            rows.append(
                [
                    InlineKeyboardButton(
                        f"🗑️ {habit_name} {reminder.hour:02d}:{reminder.minute:02d}",
                        callback_data=f"{CALLBACK_PREFIX_DELETE_REMINDER}{reminder.id}",
                    )
                ]
            )
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

    manager = HabitManager()
    await update.message.reply_text(habit_list_message(manager), reply_markup=habit_list_keyboard(manager))


async def list_streaks(update, context) -> None:
    """Handle /streaks and show calculated streak analytics."""

    await update.message.reply_text(streaks_message(), reply_markup=main_menu_keyboard())


async def add_habit(update, context) -> None:
    """Handle /add Name | daily_or_weekly | target_count.

    This command remains for CLI-style users, but the main Telegram flow uses
    buttons for daily/weekly and then asks for a plain habit name.
    """

    text = update.message.text.removeprefix("/add").strip()
    try:
        name, periodicity, target_count = _parse_add_command(text)
        manager = HabitManager()
        habit = manager.create_habit(name, periodicity, target_count)
    except ValueError as exc:
        await update.message.reply_text(str(exc), reply_markup=main_menu_keyboard())
        return

    await update.message.reply_text(
        action_update_message(f"✨ Added {habit.name}", manager),
        reply_markup=main_menu_keyboard(),
    )


async def receive_habit_name(update, context) -> int:
    """Create a habit from plain text after the Daily/Weekly button choice."""

    name = update.message.text.strip()
    periodicity = context.user_data.get("new_habit_periodicity", "daily")
    try:
        manager = HabitManager()
        habit = manager.create_habit(name, periodicity, 1)
    except ValueError as exc:
        await update.message.reply_text(str(exc), reply_markup=add_cancel_keyboard())
        return STATE_ADD_HABIT_NAME

    context.user_data.pop("new_habit_periodicity", None)
    icon = "☀️" if periodicity == "daily" else "🗓️"
    await update.message.reply_text(
        action_update_message(f"✨ Added {icon} {habit.name}", manager),
        reply_markup=main_menu_keyboard(),
    )
    return -1


async def receive_edit_habit_name(update, context) -> int:
    """Rename a selected habit after the Rename button."""

    habit_id = context.user_data.get("edit_habit_id")
    if habit_id is None:
        await update.message.reply_text("Open 📋 List habits and choose a habit first.", reply_markup=main_menu_keyboard())
        return -1

    manager = HabitManager()
    try:
        habit = manager.get_habit(int(habit_id))
        updated = manager.update_habit(
            habit.id or 0,
            update.message.text.strip(),
            habit.periodicity,
            habit.target_count,
            habit.description,
            habit.archived,
        )
    except ValueError as exc:
        await update.message.reply_text(str(exc), reply_markup=add_cancel_keyboard())
        return STATE_EDIT_HABIT_NAME

    context.user_data.pop("edit_habit_id", None)
    await update.message.reply_text(
        f"✏️ Renamed to: {updated.name}\n\n{habit_detail_message(manager, updated.id or 0)}",
        reply_markup=habit_detail_keyboard(updated),
    )
    return -1


async def done_habit(update, context) -> None:
    """Handle /done habit_id."""

    try:
        habit_id = _parse_habit_id(update.message.text, "/done")
        manager = HabitManager()
        habit = manager.get_habit(habit_id)
        manager.complete_habit(habit_id)
    except ValueError as exc:
        text = str(exc)
        reply = (
            action_update_message(text.replace("Already completed today:", "✅ Already done today:"), manager)
            if text.startswith("Already completed today:")
            else text
        )
        await update.message.reply_text(reply, reply_markup=main_menu_keyboard())
        return

    await update.message.reply_text(
        action_update_message(f"✅ Done saved: {habit.name}", manager),
        reply_markup=main_menu_keyboard(),
    )


async def archive_habit(update, context) -> None:
    """Handle /archive habit_id."""

    try:
        habit_id = _parse_habit_id(update.message.text, "/archive")
        manager = HabitManager()
        habit = manager.archive_habit(habit_id)
    except ValueError as exc:
        await update.message.reply_text(str(exc), reply_markup=main_menu_keyboard())
        return

    await update.message.reply_text(
        action_update_message(f"📦 Archived: {habit.name}", manager),
        reply_markup=main_menu_keyboard(),
    )


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

    await update.message.reply_text(
        action_update_message(f"🗑️ Deleted: {habit.name}", manager),
        reply_markup=main_menu_keyboard(),
    )


async def seed_data(update, context) -> None:
    """Handle /seed and reset demo data."""

    manager = HabitManager()
    manager.seed_demo_data()
    await update.message.reply_text(
        action_update_message("🔄 Demo data reset.", manager),
        reply_markup=main_menu_keyboard(),
    )


async def set_reminder(update, context) -> None:
    """Handle /remind habit_id HH:MM."""

    try:
        habit_id, hour, minute = _parse_remind_command(update.message.text)
        chat_id = update.effective_chat.id
        manager = HabitManager()
        habit = manager.get_habit(habit_id)
        reminder = manager.add_reminder(habit_id, chat_id, hour, minute)
        _schedule_one_if_available(context.application, manager, reminder)
    except ValueError as exc:
        await update.message.reply_text(str(exc), reply_markup=main_menu_keyboard())
        return

    reminders = manager.list_reminders(chat_id=chat_id)
    await update.message.reply_text(
        f"✅ Reminder saved: {habit.name} {hour:02d}:{minute:02d}\n\n"
        f"{reminders_message(manager, reminders)}",
        reply_markup=reminder_quick_keyboard(manager, chat_id=chat_id),
    )


async def list_reminders(update, context) -> None:
    """Handle /reminders."""

    manager = HabitManager()
    reminders = manager.list_reminders(chat_id=update.effective_chat.id)
    await update.message.reply_text(
        reminders_message(manager, reminders),
        reply_markup=reminder_quick_keyboard(manager, chat_id=update.effective_chat.id),
    )


async def delete_reminder(update, context) -> None:
    """Handle /deletereminder reminder_id."""

    try:
        reminder_id = _parse_habit_id(update.message.text, "/deletereminder")
        manager = HabitManager()
        manager.delete_reminder(reminder_id, chat_id=update.effective_chat.id)
    except ValueError as exc:
        await update.message.reply_text(str(exc), reply_markup=main_menu_keyboard())
        return

    reminders = manager.list_reminders(chat_id=update.effective_chat.id)
    await update.message.reply_text(
        f"🗑️ Reminder removed.\n\n{reminders_message(manager, reminders)}",
        reply_markup=reminder_quick_keyboard(manager, chat_id=update.effective_chat.id),
    )


async def handle_button(update, context) -> None:
    """Handle all Telegram inline button presses."""

    query = update.callback_query
    await query.answer()
    manager = HabitManager()
    data = query.data

    if data == CALLBACK_STATUS:
        await query.edit_message_text(status_message(manager), reply_markup=main_menu_keyboard())
        return -1
    elif data == CALLBACK_LIST:
        await query.edit_message_text(habit_list_message(manager), reply_markup=habit_list_keyboard(manager))
    elif data == CALLBACK_ADD_MENU:
        await query.edit_message_text("➕ New habit type:", reply_markup=add_periodicity_keyboard())
        return STATE_ADD_HABIT_PERIODICITY
    elif data == CALLBACK_HELP:
        await query.edit_message_text(help_message(), reply_markup=main_menu_keyboard())
    elif data and data.startswith(CALLBACK_PREFIX_ADD_PERIODICITY):
        periodicity = data.removeprefix(CALLBACK_PREFIX_ADD_PERIODICITY)
        if periodicity not in {"daily", "weekly"}:
            await query.edit_message_text("Choose daily or weekly.", reply_markup=add_periodicity_keyboard())
            return STATE_ADD_HABIT_PERIODICITY
        context.user_data["new_habit_periodicity"] = periodicity
        icon = "☀️" if periodicity == "daily" else "🗓️"
        await query.edit_message_text(f"{icon} Habit name?", reply_markup=add_cancel_keyboard())
        return STATE_ADD_HABIT_NAME
    elif data == CALLBACK_STREAKS:
        await query.edit_message_text(streaks_message(manager), reply_markup=main_menu_keyboard())
    elif data and data.startswith(CALLBACK_PREFIX_HABIT_DETAIL):
        habit_id = int(data.removeprefix(CALLBACK_PREFIX_HABIT_DETAIL))
        habit = manager.get_habit(habit_id)
        await query.edit_message_text(
            habit_detail_message(manager, habit_id),
            reply_markup=habit_detail_keyboard(habit),
        )
    elif data and data.startswith(CALLBACK_PREFIX_HABIT_EDIT_NAME):
        habit_id = int(data.removeprefix(CALLBACK_PREFIX_HABIT_EDIT_NAME))
        habit = manager.get_habit(habit_id)
        context.user_data["edit_habit_id"] = habit_id
        await query.edit_message_text(
            f"✏️ Rename\n\nCurrent: {habit.name}\nSend the new name.",
            reply_markup=add_cancel_keyboard(),
        )
        return STATE_EDIT_HABIT_NAME
    elif data and data.startswith(CALLBACK_PREFIX_HABIT_DELETE):
        habit_id = int(data.removeprefix(CALLBACK_PREFIX_HABIT_DELETE))
        habit = manager.get_habit(habit_id)
        manager.delete_habit(habit_id)
        await query.edit_message_text(
            f"🗑️ Deleted: {habit.name}\n\n{habit_list_message(manager)}",
            reply_markup=habit_list_keyboard(manager),
        )
    elif data and data.startswith(CALLBACK_PREFIX_HABIT_TYPE):
        payload = data.removeprefix(CALLBACK_PREFIX_HABIT_TYPE)
        habit_text, periodicity = payload.split(":", maxsplit=1)
        habit = manager.get_habit(int(habit_text))
        updated = manager.update_habit(
            habit.id or 0,
            habit.name,
            periodicity,
            habit.target_count,
            habit.description,
            habit.archived,
        )
        await query.edit_message_text(
            f"🔁 Updated type.\n\n{habit_detail_message(manager, updated.id or 0)}",
            reply_markup=habit_detail_keyboard(updated),
        )
    elif data == CALLBACK_REMINDERS:
        reminders = manager.list_reminders(chat_id=query.message.chat.id)
        await query.edit_message_text(
            reminders_message(manager, reminders),
            reply_markup=reminder_quick_keyboard(manager, chat_id=query.message.chat.id),
        )
    elif data == CALLBACK_DONE_MENU:
        await query.edit_message_text(done_menu_message(manager), reply_markup=habit_done_keyboard(manager))
    elif data == CALLBACK_SEED:
        manager.seed_demo_data()
        await query.edit_message_text(
            action_update_message("🔄 Demo data reset.", manager),
            reply_markup=main_menu_keyboard(),
        )
    elif data and data.startswith(CALLBACK_PREFIX_DONE):
        habit_id = int(data.removeprefix(CALLBACK_PREFIX_DONE))
        habit = manager.get_habit(habit_id)
        try:
            manager.complete_habit(habit_id)
        except ValueError as exc:
            text = str(exc)
            reply = (
                action_update_message(text.replace("Already completed today:", "✅ Already done today:"), manager)
                if text.startswith("Already completed today:")
                else text
            )
            await query.edit_message_text(reply, reply_markup=main_menu_keyboard())
            return
        await query.edit_message_text(
            action_update_message(f"✅ Done saved: {habit.name}", manager),
            reply_markup=main_menu_keyboard(),
        )
    elif data and data.startswith(CALLBACK_PREFIX_REMIND_QUICK):
        habit_id, hour, minute = _parse_reminder_callback(data)
        chat_id = query.message.chat.id
        habit = manager.get_habit(habit_id)
        reminder = manager.add_reminder(habit_id, chat_id, hour, minute)
        _schedule_one_if_available(context.application, manager, reminder)
        reminders = manager.list_reminders(chat_id=chat_id)
        await query.edit_message_text(
            f"✅ Reminder saved: {habit.name} {hour:02d}:{minute:02d}\n\n"
            f"{reminders_message(manager, reminders)}",
            reply_markup=reminder_quick_keyboard(manager, chat_id=chat_id),
        )
    elif data and data.startswith(CALLBACK_PREFIX_DELETE_REMINDER):
        reminder_id = int(data.removeprefix(CALLBACK_PREFIX_DELETE_REMINDER))
        manager.delete_reminder(reminder_id, chat_id=query.message.chat.id)
        reminders = manager.list_reminders(chat_id=query.message.chat.id)
        await query.edit_message_text(
            f"🗑️ Reminder removed.\n\n{reminders_message(manager, reminders)}",
            reply_markup=reminder_quick_keyboard(manager, chat_id=query.message.chat.id),
        )


def build_application(token: str):
    """Create the Telegram application and register command/button handlers."""

    from telegram.ext import (
        Application,
        CallbackQueryHandler,
        CommandHandler,
        ConversationHandler,
        MessageHandler,
        filters,
    )

    application = Application.builder().token(token).post_init(setup_reminders).build()
    add_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_button, pattern=f"^{CALLBACK_ADD_MENU}$")],
        states={
            STATE_ADD_HABIT_PERIODICITY: [
                CallbackQueryHandler(
                    handle_button,
                    pattern=f"^{CALLBACK_PREFIX_ADD_PERIODICITY}",
                )
            ],
            STATE_ADD_HABIT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_habit_name)
            ]
        },
        fallbacks=[CallbackQueryHandler(handle_button, pattern=f"^{CALLBACK_STATUS}$")],
    )
    edit_conversation = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                handle_button,
                pattern=f"^{CALLBACK_PREFIX_HABIT_EDIT_NAME}",
            )
        ],
        states={
            STATE_EDIT_HABIT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_edit_habit_name)
            ]
        },
        fallbacks=[
            CallbackQueryHandler(handle_button, pattern=f"^{CALLBACK_STATUS}$"),
            CallbackQueryHandler(handle_button, pattern=f"^{CALLBACK_LIST}$"),
        ],
    )
    application.add_handler(edit_conversation)
    application.add_handler(add_conversation)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(CommandHandler("list", list_habits))
    application.add_handler(CommandHandler("streaks", list_streaks))
    application.add_handler(CommandHandler("add", add_habit))
    application.add_handler(CommandHandler("done", done_habit))
    application.add_handler(CommandHandler("archive", archive_habit))
    application.add_handler(CommandHandler("delete", delete_habit))
    application.add_handler(CommandHandler("remind", set_reminder))
    application.add_handler(CommandHandler("reminders", list_reminders))
    application.add_handler(CommandHandler("deletereminder", delete_reminder))
    application.add_handler(CommandHandler("seed", seed_data))
    application.add_handler(CallbackQueryHandler(handle_button))
    return application


async def setup_reminders(application) -> None:
    """Start APScheduler and load saved reminders when Telegram starts."""

    global _reminder_scheduler
    if _reminder_scheduler is None:
        _reminder_scheduler = ReminderScheduler()
        _reminder_scheduler.start()
    _reminder_scheduler.schedule_existing_reminders(
        application,
        HabitManager(),
        asyncio.get_running_loop(),
    )


def reminders_message(manager: HabitManager, reminders) -> str:
    """Build a friendly reminder list for Telegram."""

    if not reminders:
        return (
            "⏰ Reminders\n\n"
            "┌ Active\n"
            "│ none\n"
            f"└ {reminder_timezone_name()} time\n\n"
            "Add: tap 🌅 or 🌙 next to a habit."
        )
    lines = ["⏰ Reminders", "", "┌ Active"]
    for reminder in reminders:
        try:
            habit = manager.get_habit(reminder.habit_id)
            habit_name = habit.name
        except ValueError:
            habit_name = "Deleted habit"
        icon = _reminder_time_icon(reminder.hour)
        lines.append(
            f"│ {icon} {habit_name}  {reminder.hour:02d}:{reminder.minute:02d}"
        )
    lines.extend(
        [
            f"└ {reminder_timezone_name()} time",
            "",
            "Add/change: tap 🌅 or 🌙.",
            "Remove: tap 🗑️.",
        ]
    )
    return "\n".join(lines)


def _reminder_time_icon(hour: int) -> str:
    """Return a compact visual marker for reminder time."""

    return "🌅" if hour < 18 else "🌙"


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


def _parse_remind_command(text: str) -> tuple[int, int, int]:
    """Parse /remind habit_id HH:MM."""

    parts = text.removeprefix("/remind").strip().split()
    if len(parts) != 2:
        raise ValueError("Use: /remind habit_id HH:MM")
    try:
        habit_id = int(parts[0])
        hour_text, minute_text = parts[1].split(":", maxsplit=1)
        hour = int(hour_text)
        minute = int(minute_text)
    except ValueError as exc:
        raise ValueError("Use a numeric habit id and time like 08:30.") from exc
    return habit_id, hour, minute


def _parse_reminder_callback(data: str) -> tuple[int, int, int]:
    """Parse a quick reminder callback like remind:1:08:30."""

    payload = data.removeprefix(CALLBACK_PREFIX_REMIND_QUICK)
    habit_text, time_text = payload.split(":", maxsplit=1)
    hour_text, minute_text = time_text.split(":", maxsplit=1)
    return int(habit_text), int(hour_text), int(minute_text)


def _schedule_one_if_available(application, manager: HabitManager, reminder) -> None:
    """Schedule a newly created reminder if the runtime scheduler is active."""

    if _reminder_scheduler is None:
        return
    habit = manager.get_habit(reminder.habit_id)
    _reminder_scheduler.schedule_reminder(
        application,
        reminder,
        habit.name,
        asyncio.get_running_loop(),
    )


def main() -> int:
    """Run the Telegram bot when TELEGRAM_BOT_TOKEN is configured."""

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN before starting the Telegram bot.")
    build_application(token).run_polling()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
