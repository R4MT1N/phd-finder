import logging
from random import choice
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, error
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, filters, \
    CallbackContext, MessageHandler
from tgbot import *
from models import Position, User, Message, UserPosition

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# async def notify_future_positions(title="Day", days=1, weeks=0, months=0):
#     rel_delta = relativedelta(days=days, weeks=weeks, months=months)
#     num_positions = Position.near_deadlines(rel_delta, count=True)
#
#     if not num_positions:
#         return
#
#     total_pages = ceil(num_positions / Position.PER_PAGE)
#
#     for page in range(1, total_pages + 1):
#         lines = [f"⭐️ *{title} Deadlines{f' {page}/{total_pages}' if total_pages > 1 else ''}* ⭐️"]
#
#         for position in Position.near_deadlines(rel_delta, page=page):
#             lines += [f"\n{markdown_compact_position(tgbot.username, chat_id, position)}"]
#
#         await tgbot.send_message(chat_id, '\n'.join(lines), ParseMode.MARKDOWN, disable_web_page_preview=True)
#         time.sleep(1)

async def remove_channel_position_inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    position_id = query.data.split(COMMAND_SEP)[1]

    if (user := User.get_or_none(id=query.from_user.id, is_admin=True)) is None:
        await query.answer(ONLY_ADMINS_ALLOWED, show_alert=True)
        return

    if (position := Position.get_or_none(id=position_id)) is None:
        await query.answer(POSITION_ID_INVALID.format(position_id), show_alert=True)
        return

    position.remove()
    await query.answer(POSITION_REMOVED, show_alert=True)
    await query.message.delete()

async def watch_channel_position_inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    position_id = query.data.split(COMMAND_SEP)[1]

    if (user := User.get_or_none(id=query.from_user.id)) is None:
        await query.answer(ONLY_REGISTERED_USER_ALLOWED, show_alert=True)
        return

    if (position := Position.get_or_none(id=position_id)) is None:
        await query.answer(POSITION_ID_INVALID.format(position_id), show_alert=True)
        return

    if UserPosition.select().where((UserPosition.position == position) & (UserPosition.user == user)).exists():
        await query.answer(POSITION_ALREADY_IN_LIST, show_alert=True)
        return

    user.positions.add(position)
    await query.answer(POSITION_ADDED_TO_LIST, show_alert=True)

async def cancel_inline_handler(update: Update, context: CallbackContext):
    query = update.callback_query

    if (user := User.get_by_id(query.from_user.id)) is None:
        await update.message.reply_text(ONLY_REGISTERED_USER_ALLOWED)
        return

    await remove_message(query, user)

# -------------------------------------------------------------

async def unwatch_position_command_handler(update: Update, context: CallbackContext):
    position_id = update.message.text.replace(f'/{UNWATCH_COMMAND}', '')

    if (user := User.get_by_id(update.effective_user.id)) is None:
        await update.message.reply_text(ONLY_REGISTERED_USER_ALLOWED)
        return

    if (position := Position.get_or_none(id=position_id)) is None:
        await update.message.reply_text(POSITION_ID_INVALID.format(position_id))
        return

    user.positions.remove(position)

    keyboard = [
        [InlineKeyboardButton(UNDO_BTN, callback_data=f'{UNDO_UNWATCH_POSITION_INLINE}{COMMAND_SEP}{position.id}'),
         InlineKeyboardButton(NVM_BTN, callback_data=f'{CANCEL_INLINE}')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    message = await update.message.reply_text(POSITION_UNWATCHED.format(position.title), parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    Message.add(user, message.id)

async def undo_unwatch_position_inline_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    position_id = query.data.split(COMMAND_SEP)[1]

    if (user := User.get_by_id(query.from_user.id)) is None:
        await update.message.reply_text(ONLY_REGISTERED_USER_ALLOWED)
        return

    if (position := Position.get_or_none(id=position_id)) is None:
        await query.answer(POSITION_ID_INVALID.format(position_id), show_alert=True)
        return

    if UserPosition.select().where((UserPosition.position == position) & (UserPosition.user == user)).exists():
        await query.answer(POSITION_ALREADY_IN_LIST, show_alert=True)
    else:
        user.positions.add(position)
        await query.answer(POSITION_ADDED_TO_LIST, show_alert=True)

    await remove_message(query, user)

async def restore_position_command_handler(update: Update, context: CallbackContext):
    position_id = update.message.text.replace(f'/{RESTORE_COMMAND}', '')

    if (user := User.get_by_id(update.effective_user.id)) is None or not user.is_admin:
        await update.message.reply_text(ONLY_ADMINS_ALLOWED)
        return

    if (position := Position.get_or_none(id=position_id)) is None:
        await update.message.reply_text(POSITION_ID_INVALID.format(position_id))
        return

    position.restore()
    await publish_position(context.bot, CHANNEL_CHAT_ID, position, True)

    message = await update.message.reply_text(POSITION_RESTORED.format(position.title), parse_mode=ParseMode.MARKDOWN)
    Message.add(user, message.id)

async def undo_restore_position_inline_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    position_id = query.data.split(COMMAND_SEP)[1]

    if (user := User.get_by_id(query.from_user.id)) is None or not user.is_admin:
        await update.message.reply_text(ONLY_ADMINS_ALLOWED)
        return

    if (position := Position.get_or_none(id=position_id)) is None:
        await query.answer(POSITION_ID_INVALID.format(position_id), show_alert=True)
        return

    if position.removed_at is not None:
        await query.answer(POSITION_ALREADY_REMOVED, show_alert=True)
    else:
        position.remove()
        await query.answer(POSITION_REMOVED, show_alert=True)

    await remove_message(query, user)

# -------------------------------------------------------------

async def welcome_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id, chat_id = update.effective_user.id, update.effective_chat.id

    if (user := User.get_or_none(id=user_id)) is None:
        await update.message.reply_text('You are not a registered user. Ask an admin to do the registration.')
        return

    if user.chat_id is None:
        user.update_chat_id(chat_id)
        await update.message.reply_text('You are good to go! Now check positions in the channel and add some of them into your watchlist.')
    else:
        await update.message.reply_text(choice(start_funny_sentences))

async def my_ongoing_positions_intro_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    page = 1

    if (user := User.get_or_none(id=update.effective_user.id)) is None:
        await update.message.reply_text(ONLY_REGISTERED_USER_ALLOWED)
        return

    text, reply_markup = my_ongoing_positions(user, page, 5)

    await update.message.reply_text(text, ParseMode.MARKDOWN, reply_markup=reply_markup, disable_web_page_preview=True)

async def my_ongoing_positions_inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    page = resolve_page(query.data.split(COMMAND_SEP)[1])

    if (user := User.get_or_none(id=query.from_user.id)) is None:
        await update.message.reply_text(ONLY_REGISTERED_USER_ALLOWED)
        return

    text, reply_markup = my_ongoing_positions(user, page, 5)

    try:
        await query.edit_message_text(text, ParseMode.MARKDOWN, reply_markup=reply_markup, disable_web_page_preview=True)
    except error.BadRequest:
        await query.answer(NOTHING_CHANGED)

async def my_expired_positions_intro_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    page = '1'

    if (user := User.get_or_none(id=update.effective_user.id)) is None:
        await update.message.reply_text(ONLY_REGISTERED_USER_ALLOWED)
        return

    text, reply_markup = my_expired_positions(user, page, 5)

    await update.message.reply_text(text, ParseMode.MARKDOWN, reply_markup=reply_markup, disable_web_page_preview=True)

async def my_expired_positions_inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    page = resolve_page(query.data.split(COMMAND_SEP)[1])

    if (user := User.get_or_none(id=query.from_user.id)) is None:
        await query.edit_message_text(ONLY_REGISTERED_USER_ALLOWED, ParseMode.MARKDOWN, reply_markup=None)
        return

    text, reply_markup = my_expired_positions(user, page, 5)

    try:
        await query.edit_message_text(text, ParseMode.MARKDOWN, reply_markup=reply_markup, disable_web_page_preview=True)
    except error.BadRequest:
        await query.answer(NOTHING_CHANGED)

async def removed_positions_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    page = '1'

    if (user := User.get_or_none(id=update.effective_user.id)) is None or not user.is_admin:
        await update.message.reply_text(ONLY_ADMINS_ALLOWED, ParseMode.MARKDOWN)
        return

    text, reply_markup = removed_positions(page, 5)

    await update.message.reply_text(text, ParseMode.MARKDOWN, reply_markup=reply_markup, disable_web_page_preview=True)

async def removed_positions_inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    page = resolve_page(query.data.split(COMMAND_SEP)[1])

    if (user := User.get_or_none(id=query.from_user.id)) is None or not user.is_admin:
        await query.edit_message_text(ONLY_ADMINS_ALLOWED, ParseMode.MARKDOWN, reply_markup=None)
        return

    text, reply_markup = removed_positions(page, 5)

    try:
        await query.edit_message_text(text, ParseMode.MARKDOWN, reply_markup=reply_markup, disable_web_page_preview=True)
    except error.BadRequest:
        await query.answer(NOTHING_CHANGED)

async def weekly_reminder_inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    page = resolve_page(query.data.split(COMMAND_SEP)[1])

    if (user := User.get_or_none(id=query.from_user.id)) is None:
        await query.edit_message_text(ONLY_REGISTERED_USER_ALLOWED, ParseMode.MARKDOWN, reply_markup=None)
        return

    text, reply_markup = upcoming_week_positions(user, page, 5)

    try:
        await query.edit_message_text(text, ParseMode.MARKDOWN, reply_markup=reply_markup, disable_web_page_preview=True)
    except error.BadRequest:
        await query.answer(NOTHING_CHANGED)

async def daily_reminder_inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    page = resolve_page(query.data.split(COMMAND_SEP)[1])

    if (user := User.get_or_none(id=query.from_user.id)) is None:
        await query.edit_message_text(ONLY_REGISTERED_USER_ALLOWED, ParseMode.MARKDOWN, reply_markup=None)
        return

    text, reply_markup = upcoming_day_positions(user, page, 5)

    try:
        await query.edit_message_text(text, ParseMode.MARKDOWN, reply_markup=reply_markup,
                                      disable_web_page_preview=True)
    except error.BadRequest:
        await query.answer(NOTHING_CHANGED)


def main() -> None:
    application = Application.builder().token(TG_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", welcome_command_handler))
    application.add_handler(CommandHandler(MY_ONGOING_POSITIONS_COMMAND, my_ongoing_positions_intro_command_handler))
    application.add_handler(CommandHandler(MY_EXPIRED_POSITIONS_COMMAND, my_expired_positions_intro_command_handler))
    application.add_handler(CommandHandler(REMOVED_POSITIONS_COMMAND, removed_positions_command_handler))

    application.add_handler(MessageHandler(filters.Regex(fr'^/{UNWATCH_COMMAND}'), unwatch_position_command_handler))
    # application.add_handler(MessageHandler(filters.Regex(fr'^/{REMOVE_COMMAND}'), remove_position_command_handler))
    application.add_handler(MessageHandler(filters.Regex(fr'^/{RESTORE_COMMAND}'), restore_position_command_handler))

    application.add_handler(CallbackQueryHandler(watch_channel_position_inline_handler, WATCH_CHANNEL_POSITION_INLINE))
    application.add_handler(CallbackQueryHandler(remove_channel_position_inline_handler, REMOVE_CHANNEL_POSITION_INLINE))

    # application.add_handler(CallbackQueryHandler(undo_watch_position_inline_handler, UNDO_WATCH_POSITION_INLINE))
    application.add_handler(CallbackQueryHandler(undo_unwatch_position_inline_handler, UNDO_UNWATCH_POSITION_INLINE))
    # application.add_handler(CallbackQueryHandler(undo_remove_position_inline_handler, UNDO_REMOVE_POSITION_INLINE))
    application.add_handler(CallbackQueryHandler(undo_restore_position_inline_handler, UNDO_RESTORE_POSITION_INLINE))
    application.add_handler(CallbackQueryHandler(my_ongoing_positions_inline_handler, MY_ONGOING_POSITIONS_INLINE))
    application.add_handler(CallbackQueryHandler(my_expired_positions_inline_handler, MY_EXPIRED_POSITIONS_INLINE))
    application.add_handler(CallbackQueryHandler(removed_positions_inline_handler, REMOVED_POSITIONS_INLINE))
    application.add_handler(CallbackQueryHandler(weekly_reminder_inline_handler, UPCOMING_WEEK_DEADLINES_INLINE))
    application.add_handler(CallbackQueryHandler(daily_reminder_inline_handler, UPCOMING_DAY_DEADLINES_INLINE))

    application.add_handler(CallbackQueryHandler(cancel_inline_handler, CANCEL_INLINE))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
