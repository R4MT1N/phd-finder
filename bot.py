import logging
from pathlib import Path
from random import choice
from dotenv import load_dotenv
from peewee import DoesNotExist
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, error
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, filters, \
    CallbackContext, MessageHandler
from models import Position, User, Message, UserPosition
from tgbot import *

load_dotenv(Path(__file__).parent.joinpath('.env'), override=True)

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
    position_id = query.data.split('+')[1]

    if (user := User.get_or_none(id=query.from_user.id, is_admin=True)) is None:
        await query.answer('Only admins can do that', show_alert=True)
        return

    if user.chat_id is None:
        await query.answer('You have to start the bot first', show_alert=True)
        return

    try:
        position: Position = Position.get_by_id(position_id)
    except DoesNotExist:
        await query.answer(f'Position id ({position_id}) is invalid', show_alert=True)
        return

    await query.answer()
    await query.message.delete()
    position.remove()

    keyboard = [
        [InlineKeyboardButton("⬅️ Undo", callback_data=f'{UNDO_REMOVE_POSITION_INLINE}+{position.id}'),
         InlineKeyboardButton("I'm OK", callback_data=f'{CANCEL_INLINE}+')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    message = await context.bot.send_message(user.chat_id, f'Position "{position.title}" is removed.', reply_markup=reply_markup)
    Message.add(user, message.id)

async def watch_channel_position_inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    position_id = query.data.split('+')[1]

    try:
        user = User.get_by_id(query.from_user.id)
    except DoesNotExist:
        await query.answer('You are not registered yet', show_alert=True)
        return

    if user.chat_id is None:
        await query.answer('You have to start the tgbot first', show_alert=True)
        return

    try:
        position = Position.get_by_id(position_id)
    except DoesNotExist:
        await query.answer(f'Position id ({position_id}) is invalid', show_alert=True)
        return

    if UserPosition.select().where((UserPosition.position == position) & (UserPosition.user == user)).exists():
        await query.answer(f'Position is already in your watchlist', show_alert=True)
        return

    user.positions.add(position)
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("⬅️ Undo", callback_data=f'{UNDO_WATCH_POSITION_INLINE}+{position.id}'),
         InlineKeyboardButton("I'm OK", callback_data=f'{CANCEL_INLINE}')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    message = await context.bot.send_message(user.chat_id, f'Position "{position.title}" is added to watchlist.', reply_markup=reply_markup)
    Message.add(user, message.id)

# -------------------------------------------------------------

async def undo_remove_position_inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    position_id = query.data.split('+')[1]
    user = User.get_by_id(query.from_user.id)

    if not user.is_admin:
        await query.answer('Only admins can do that', show_alert=True)
        await remove_message(query, user)
        return

    try:
        position = Position.get_by_id(position_id)
        position.restore()
        await publish_position(context.bot, CHANNEL_CHAT_ID, position, True)
        await query.answer("Position is restored", show_alert=True)
    except DoesNotExist:
        await query.answer(f'Position id ({position_id}) is invalid', show_alert=True)

    await remove_message(query, user)

async def undo_watch_position_inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    position_id = query.data.split('+')[1]

    user = User.get_by_id(query.from_user.id)

    try:
        position = Position.get_by_id(position_id)
    except DoesNotExist:
        await query.answer(f'Position id ({position_id}) is invalid', show_alert=True)
        await remove_message(query, user)
        return

    if not UserPosition.select().where((UserPosition.position == position) & (UserPosition.user == user)).exists():
        await query.answer(f'Position is already NOT in your watchlist', show_alert=True)
    else:
        user.positions.remove(position)
        await query.answer("Position is removed from watchlist", show_alert=True)

    await remove_message(query, user)

async def undo_unwatch_position_inline_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    position_id = query.data.split('+')[1]
    user = User.get_by_id(query.from_user.id)

    try:
        position = Position.get_by_id(position_id)
    except DoesNotExist:
        await query.answer(f'Position id ({position_id}) is invalid', show_alert=True)
        await remove_message(query, user)
        return

    if UserPosition.select().where((UserPosition.position == position) & (UserPosition.user == user)).exists():
        await query.answer(f'Position is already in your watchlist', show_alert=True)
    else:
        user.positions.add(position)
        await query.answer('Position is added to watchlist, again!', show_alert=True)

    await remove_message(query, user)

async def undo_restore_position_inline_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    position_id = query.data.split('+')[1]
    user = User.get_by_id(query.from_user.id)

    try:
        position = Position.get_by_id(position_id)
    except DoesNotExist:
        await query.answer(f'Position id ({position_id}) is invalid', show_alert=True)
        await remove_message(query, user)
        return

    if position.removed_at is not None:
        await query.answer(f'Position is already removed', show_alert=True)
    else:
        position.remove()
        await query.answer('Position is removed, again!', show_alert=True)

    await remove_message(query, user)

async def cancel_inline_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user = User.get_by_id(query.from_user.id)

    await remove_message(query, user)

# -------------------------------------------------------------

# async def remove_position_command_handler(update: Update, context: CallbackContext):
#     position_id = update.message.text.replace(f'/{REMOVE_COMMAND}', '')
#     user_id = update.effective_user.id
#
#     try:
#         if (user := User.get_or_none(id=user_id, is_admin=True)) is None:
#             raise DoesNotExist()
#     except DoesNotExist:
#         await update.message.reply_text('Only admins can do that')
#         return
#
#     try:
#         position = Position.get_by_id(position_id)
#     except DoesNotExist:
#         await update.message.reply_text('The position is invalid')
#         return
#
#     position.remove()
#
#     keyboard = [
#         [InlineKeyboardButton("⬅️ Undo", callback_data=f'{UNDO_REMOVE_POSITION_INLINE}+{position.id}'),
#          InlineKeyboardButton("I'm OK", callback_data=f'{CANCEL_INLINE}')]
#     ]
#
#     reply_markup = InlineKeyboardMarkup(keyboard)
#
#     message = await update.message.reply_text(f'Position "{position.title}" is removed.', parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
#     Message.add(user, message.id)

async def unwatch_position_command_handler(update: Update, context: CallbackContext):
    position_id = update.message.text.replace(f'/{UNWATCH_COMMAND}', '')
    user = User.get_by_id(update.effective_user.id)

    try:
        position = Position.get_by_id(position_id)
    except DoesNotExist:
        await update.message.reply_text(f'The position id ({position_id}) is invalid')
        return

    user.positions.remove(position)

    keyboard = [
        [InlineKeyboardButton("⬅️ Undo", callback_data=f'{UNDO_UNWATCH_POSITION_INLINE}+{position.id}'),
         InlineKeyboardButton("I'm OK", callback_data=f'{CANCEL_INLINE}')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    message = await update.message.reply_text(f'Position "{position.title}" is removed from watchlist.', parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    Message.add(user, message.id)

async def restore_position_command_handler(update: Update, context: CallbackContext):
    position_id = update.message.text.replace(f'/{RESTORE_COMMAND}', '')
    user = User.get_by_id(update.effective_user.id)

    if not user.is_admin:
        await update.message.reply_text('Only admins can do that')
        return

    try:
        position = Position.get_by_id(position_id)
    except DoesNotExist:
        await update.message.reply_text('The position is invalid')
        return

    position.restore()
    await publish_position(context.bot, CHANNEL_CHAT_ID, position, True)

    # keyboard = [
    #     [InlineKeyboardButton("⬅️ Undo", callback_data=f'{UNDO_RESTORE_POSITION_INLINE}+{position.id}'),
    #      InlineKeyboardButton("I'm OK", callback_data=f'{CANCEL_INLINE}')]
    # ]

    # reply_markup = InlineKeyboardMarkup(keyboard)
    message = await update.message.reply_text(f'Position "{position.title}" is restored.', parse_mode=ParseMode.MARKDOWN)

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
    user_id = update.effective_user.id
    page = '1'

    if (user := User.get_or_none(id=user_id)) is None:
        await update.message.reply_text('You are not a registered user. Ask an admin to do the registration.')
        return

    num_live_positions = user.ongoing_positions(count=True)

    if num_live_positions == 0:
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔄 Refresh", callback_data=f'{MY_ONGOING_POSITIONS_INLINE}+1')]])
        await update.message.reply_text('You have no ongoing positions.', reply_markup=reply_markup)
        return

    text, reply_markup = my_ongoing_positions(user, page, 5, num_live_positions)

    await update.message.reply_text(text, ParseMode.MARKDOWN, reply_markup=reply_markup, disable_web_page_preview=True)

async def my_ongoing_positions_inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    query = update.callback_query
    page = query.data.split('+')[1]

    if (user := User.get_or_none(id=user_id)) is None:
        await query.edit_message_text('You are not a registered user. Ask an admin to do the registration.', ParseMode.MARKDOWN, reply_markup=None)
        return

    num_positions = user.ongoing_positions(count=True)

    if num_positions == 0:
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔄 Refresh", callback_data=f'{MY_ONGOING_POSITIONS_INLINE}+1')]])
        await query.edit_message_text('You have no ongoing positions.', ParseMode.MARKDOWN, reply_markup=reply_markup)
        return

    text, reply_markup = my_ongoing_positions(user, page, 5, num_positions)

    try:
        await query.edit_message_text(text, ParseMode.MARKDOWN, reply_markup=reply_markup, disable_web_page_preview=True)
    except error.BadRequest:
        await query.answer('Nothing has changed since yet.')

async def my_expired_positions_intro_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    page = '1'

    if (user := User.get_or_none(id=user_id)) is None:
        await update.message.reply_text('You are not a registered user. Ask an admin to do the registration.')
        return

    num_positions = user.expired_positions(count=True)

    if num_positions == 0:
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔄 Refresh", callback_data=f'{MY_EXPIRED_POSITIONS_INLINE}+1')]])
        await update.message.reply_text('You have no expired positions.', reply_markup=reply_markup)
        return

    text, reply_markup = my_expired_positions(user, page, 5, num_positions)
    await update.message.reply_text(text, ParseMode.MARKDOWN, reply_markup=reply_markup, disable_web_page_preview=True)

async def my_expired_positions_inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    query = update.callback_query
    page = query.data.split('+')[1]

    if (user := User.get_or_none(id=user_id)) is None:
        await query.edit_message_text('You are not a registered user. Ask an admin to do the registration.',
                                      ParseMode.MARKDOWN, reply_markup=None)
        return

    num_positions = user.expired_positions(count=True)

    if num_positions == 0:
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔄 Refresh", callback_data=f'{MY_EXPIRED_POSITIONS_INLINE}+1')]])
        await query.edit_message_text('You have no expired positions.', ParseMode.MARKDOWN, reply_markup=reply_markup)
        return

    text, reply_markup = my_expired_positions(user, page, 5, num_positions)

    try:
        await query.edit_message_text(text, ParseMode.MARKDOWN, reply_markup=reply_markup, disable_web_page_preview=True)
    except error.BadRequest:
        await query.answer('Nothing has changed since yet.')

async def removed_positions_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    page = '1'

    if (user := User.get_or_none(id=user_id)) is None:
        await update.message.reply_text('You are not a registered user. Ask an admin to do the registration.', ParseMode.MARKDOWN, reply_markup=None)
        return

    num_positions = Position.removed(count=True)

    if num_positions == 0:
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔄 Refresh", callback_data=f'{REMOVED_POSITIONS_INLINE}+1')]])
        await update.message.reply_text('No removed positions were found.', ParseMode.MARKDOWN, reply_markup=reply_markup)
        return

    text, reply_markup = removed_positions(user, page, 5, num_positions)
    await update.message.reply_text(text, ParseMode.MARKDOWN, reply_markup=reply_markup, disable_web_page_preview=True)

async def removed_positions_inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    query = update.callback_query
    page = query.data.split('+')[1]

    if (user := User.get_or_none(id=user_id)) is None:
        await query.edit_message_text('You are not a registered user. Ask an admin to do the registration.',
                                      ParseMode.MARKDOWN, reply_markup=None)
        return

    num_positions = Position.removed(count=True)

    if num_positions == 0:
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔄 Refresh", callback_data=f'{REMOVED_POSITIONS_INLINE}+1')]])
        await query.edit_message_text('No removed positions were found.', ParseMode.MARKDOWN, reply_markup=reply_markup)
        return

    text, reply_markup = removed_positions(user, page, 5, num_positions)

    try:
        await query.edit_message_text(text, ParseMode.MARKDOWN, reply_markup=reply_markup,
                                      disable_web_page_preview=True)
    except error.BadRequest:
        await query.answer('Nothing has changed since yet.')


def main() -> None:
    application = Application.builder().token(os.getenv('TG_BOT_TOKEN')).build()

    application.add_handler(CommandHandler("start", welcome_command_handler))
    application.add_handler(CommandHandler(MY_ONGOING_POSITIONS_COMMAND, my_ongoing_positions_intro_command_handler))
    application.add_handler(CommandHandler(MY_EXPIRED_POSITIONS_COMMAND, my_expired_positions_intro_command_handler))
    application.add_handler(CommandHandler(REMOVED_POSITIONS_COMMAND, removed_positions_command_handler))

    application.add_handler(MessageHandler(filters.Regex(fr'^/{UNWATCH_COMMAND}'), unwatch_position_command_handler))
    # application.add_handler(MessageHandler(filters.Regex(fr'^/{REMOVE_COMMAND}'), remove_position_command_handler))
    application.add_handler(MessageHandler(filters.Regex(fr'^/{RESTORE_COMMAND}'), restore_position_command_handler))

    application.add_handler(CallbackQueryHandler(undo_watch_position_inline_handler, UNDO_WATCH_POSITION_INLINE))
    application.add_handler(CallbackQueryHandler(undo_unwatch_position_inline_handler, UNDO_UNWATCH_POSITION_INLINE))
    application.add_handler(CallbackQueryHandler(undo_remove_position_inline_handler, UNDO_REMOVE_POSITION_INLINE))
    application.add_handler(CallbackQueryHandler(undo_restore_position_inline_handler, UNDO_RESTORE_POSITION_INLINE))

    application.add_handler(CallbackQueryHandler(my_ongoing_positions_inline_handler, MY_ONGOING_POSITIONS_INLINE))
    application.add_handler(CallbackQueryHandler(my_expired_positions_inline_handler, MY_EXPIRED_POSITIONS_INLINE))
    application.add_handler(CallbackQueryHandler(removed_positions_inline_handler, REMOVED_POSITIONS_INLINE))

    application.add_handler(CallbackQueryHandler(cancel_inline_handler, CANCEL_INLINE))

    application.add_handler(CallbackQueryHandler(watch_channel_position_inline_handler, WATCH_CHANNEL_POSITION_INLINE))
    application.add_handler(CallbackQueryHandler(remove_channel_position_inline_handler, REMOVE_CHANNEL_POSITION_INLINE))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
