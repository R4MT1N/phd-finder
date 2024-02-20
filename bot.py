import logging
from random import choice
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, error, ReplyKeyboardMarkup, \
    InlineQueryResultArticle, InputTextMessageContent, InlineQueryResultsButton
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, filters, \
    CallbackContext, MessageHandler, InlineQueryHandler
from tgbot import *
from models import Position, User, Message, UserPosition, University

UNIVERSITY_PER_PAGE = 10
POSITION_PER_PAGE = 7

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def generate_keyboard_buttons(is_admin: bool):
    buttons = [[ONGOING_POSITIONS_COMMAND, EXPIRED_POSITIONS_COMMAND]]

    if is_admin:
        buttons.append([UNIVERSITIES_COMMAND, REMOVED_POSITIONS_COMMAND])
    else:
        buttons.append([UNIVERSITIES_COMMAND])

    return ReplyKeyboardMarkup(buttons, one_time_keyboard=False, resize_keyboard=True, is_persistent=False)

async def remove_channel_position_inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    position_id = query.data.split(COMMAND_SEP)[1]

    if (user := User.get_or_none(id=query.from_user.id, is_admin=True)) is None:
        await query.answer(ONLY_ADMINS_ALLOWED)
        return

    if (position := Position.get_or_none(id=position_id)) is None:
        await query.answer(POSITION_ID_INVALID.format(position_id))
    else:
        position.remove()
        await query.answer(POSITION_REMOVED)

    await query.message.delete()

async def watch_channel_position_inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    position_id = query.data.split(COMMAND_SEP)[1]

    if (user := User.get_or_none(id=query.from_user.id)) is None:
        await query.answer(ONLY_REGISTERED_USER_ALLOWED)
        return

    if (position := Position.get_or_none(id=position_id)) is None:
        await query.answer(POSITION_ID_INVALID.format(position_id))
        return

    if UserPosition.select().where((UserPosition.position == position) & (UserPosition.user == user)).exists():
        await query.answer(POSITION_ALREADY_IN_LIST)
        return

    user.positions.add(position)
    await query.answer(POSITION_WATCHED)

async def cancel_inline_handler(update: Update, context: CallbackContext):
    query = update.callback_query

    if (user := User.get_by_id(query.from_user.id)) is None:
        await update.message.reply_text(ONLY_REGISTERED_USER_ALLOWED)
        return

    await remove_message(query, user)

# -------------------------------------------------------------

async def welcome_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id, chat_id = update.effective_user.id, update.effective_chat.id

    if (user := User.get_or_none(id=user_id)) is None:
        await update.message.reply_text('You are not a registered user. Ask an admin to do the registration.')
        return

    if user.chat_id is None:
        user.update_chat_id(chat_id)
        await update.message.reply_text('You are good to go! Now check positions in the channel and add some of them into your watchlist.', reply_markup=generate_keyboard_buttons(user.is_admin))
    else:
        await update.message.reply_text(choice(start_funny_sentences), reply_markup=generate_keyboard_buttons(user.is_admin))

async def watch_position_command_handler(update: Update, context: CallbackContext):
    position_id = update.message.text.replace(f'/{WATCH_COMMAND}', '')

    logger.info(f'watch position id={position_id}')

    if (user := User.get_by_id(update.effective_user.id)) is None:
        await update.message.reply_text(ONLY_REGISTERED_USER_ALLOWED)
        return

    if (position := Position.get_or_none(id=position_id)) is None:
        await update.message.reply_text(POSITION_ID_INVALID.format(position_id))
        return

    if UserPosition.select().where((UserPosition.position == position) & (UserPosition.user == user)).exists():
        await update.message.reply_text(POSITION_ALREADY_IN_LIST)
        return

    user.positions.add(position)

    keyboard = [
        [InlineKeyboardButton(UNDO_BTN, callback_data=f'{UNDO_WATCH_POSITION_INLINE}{COMMAND_SEP}{position.id}'),
         InlineKeyboardButton(NVM_BTN, callback_data=f'{CANCEL_INLINE}')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    message = await update.message.reply_text(POSITION_TITLE_WATCHED.format(position.title), parse_mode=ParseMode.MARKDOWN_V2, reply_markup=reply_markup, quote=True)
    Message.add(user, message.id)

async def unwatch_position_command_handler(update: Update, context: CallbackContext):
    position_id = update.message.text.replace(f'/{UNWATCH_COMMAND}', '')

    logger.info(f'Unwatch position id={position_id}')

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

    message = await update.message.reply_text(POSITION_UNWATCHED.format(position.title), parse_mode=ParseMode.MARKDOWN_V2, reply_markup=reply_markup, quote=True)
    Message.add(user, message.id)

async def restore_position_command_handler(update: Update, context: CallbackContext):
    position_id = update.message.text.replace(f'/{RESTORE_COMMAND}', '')

    logger.info(f'Restore position id={position_id}')

    if (user := User.get_by_id(update.effective_user.id)) is None or not user.is_admin:
        await update.message.reply_text(ONLY_ADMINS_ALLOWED)
        return

    if (position := Position.get_or_none(id=position_id)) is None:
        await update.message.reply_text(POSITION_ID_INVALID.format(position_id))
        return

    position.restore()
    await publish_position(context.bot, CHANNEL_CHAT_ID, position, True)

    message = await update.message.reply_text(POSITION_RESTORED.format(position.title), parse_mode=ParseMode.MARKDOWN_V2, quote=True)
    Message.add(user, message.id)

async def university_positions_intro_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    university_id = parse_int(update.message.text.replace(f'/{UNIVERSITY_POSITIONS_COMMAND}', ''), default=1)
    page = 1

    logger.info(f'University positions id={university_id}')

    if (user := User.get_or_none(id=update.effective_user.id)) is None:
        await update.message.reply_text(ONLY_REGISTERED_USER_ALLOWED)
        return

    if (university := University.get_or_none(university_id)) is None:
        await update.message.reply_text(UNIVERSITY_ID_INVALID)
        return

    text, reply_markup = university_positions(user, university, page, POSITION_PER_PAGE)

    await update.message.reply_text(text, ParseMode.MARKDOWN_V2, reply_markup=reply_markup, disable_web_page_preview=True, quote=True)

async def my_ongoing_positions_intro_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    page = 1

    if (user := User.get_or_none(id=update.effective_user.id)) is None:
        await update.message.reply_text(ONLY_REGISTERED_USER_ALLOWED, quote=True)
        return

    text, reply_markup = my_ongoing_positions(user, page, POSITION_PER_PAGE)

    await update.message.reply_text(text, ParseMode.MARKDOWN_V2, reply_markup=reply_markup, disable_web_page_preview=True, quote=True)

async def my_expired_positions_intro_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    page = 1

    if (user := User.get_or_none(id=update.effective_user.id)) is None:
        await update.message.reply_text(ONLY_REGISTERED_USER_ALLOWED, quote=True)
        return

    text, reply_markup = my_expired_positions(user, page, POSITION_PER_PAGE)

    await update.message.reply_text(text, ParseMode.MARKDOWN_V2, reply_markup=reply_markup, disable_web_page_preview=True, quote=True)

async def removed_positions_intro_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    page = 1

    if (user := User.get_or_none(id=update.effective_user.id)) is None or not user.is_admin:
        await update.message.reply_text(ONLY_ADMINS_ALLOWED, quote=True)
        return

    text, reply_markup = removed_positions(user, page, POSITION_PER_PAGE)

    await update.message.reply_text(text, ParseMode.MARKDOWN_V2, reply_markup=reply_markup, disable_web_page_preview=True, quote=True)

async def universities_intro_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    page = 1

    if (user := User.get_or_none(id=update.effective_user.id)) is None:
        await update.message.reply_text(ONLY_REGISTERED_USER_ALLOWED)
        return

    text, reply_markup = university_list(page, UNIVERSITY_PER_PAGE)

    await update.message.reply_text(text, ParseMode.MARKDOWN_V2, reply_markup=reply_markup, disable_web_page_preview=True, quote=True)

# -------------------------------------------------------------

async def university_positions_inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    page = parse_int(query.data.split(COMMAND_SEP)[2], default=1)
    university_id = parse_int(query.data.split(COMMAND_SEP)[1], default=1)

    if (user := User.get_or_none(id=query.from_user.id)) is None:
        await update.message.reply_text(ONLY_REGISTERED_USER_ALLOWED)
        return

    if (university := University.get_or_none(university_id)) is None:
        await update.message.reply_text(UNIVERSITY_ID_INVALID)
        return

    text, reply_markup = university_positions(user, university, page, POSITION_PER_PAGE)

    try:
        await query.edit_message_text(text, ParseMode.MARKDOWN_V2, reply_markup=reply_markup, disable_web_page_preview=True)
    except error.BadRequest as e:
        logger.error(e.message)
        await query.answer(NOTHING_CHANGED)

async def universities_inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    page = parse_int(query.data.split(COMMAND_SEP)[1], default=1)

    if (user := User.get_or_none(id=query.from_user.id)) is None:
        await update.message.reply_text(ONLY_REGISTERED_USER_ALLOWED)
        return

    text, reply_markup = university_list(page, UNIVERSITY_PER_PAGE)

    try:
        await query.edit_message_text(text, ParseMode.MARKDOWN_V2, reply_markup=reply_markup, disable_web_page_preview=True)
    except error.BadRequest as e:
        logger.error(e.message)
        await query.answer(NOTHING_CHANGED)

async def undo_unwatch_position_inline_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    position_id = query.data.split(COMMAND_SEP)[1]

    if (user := User.get_by_id(query.from_user.id)) is None:
        await update.message.reply_text(ONLY_REGISTERED_USER_ALLOWED)
        return

    if (position := Position.get_or_none(id=position_id)) is None:
        await query.answer(POSITION_ID_INVALID.format(position_id))
        return

    if UserPosition.select().where((UserPosition.position == position) & (UserPosition.user == user)).exists():
        await query.answer(POSITION_ALREADY_IN_LIST)
    else:
        user.positions.add(position)
        await query.answer(POSITION_WATCHED)

    await remove_message(query, user)

async def undo_restore_position_inline_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    position_id = query.data.split(COMMAND_SEP)[1]

    if (user := User.get_by_id(query.from_user.id)) is None or not user.is_admin:
        await update.message.reply_text(ONLY_ADMINS_ALLOWED)
        return

    if (position := Position.get_or_none(id=position_id)) is None:
        await query.answer(POSITION_ID_INVALID.format(position_id))
        return

    if position.removed_at is not None:
        await query.answer(POSITION_ALREADY_REMOVED)
    else:
        position.remove()
        await query.answer(POSITION_REMOVED)

    await remove_message(query, user)

async def my_ongoing_positions_inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    page = parse_int(query.data.split(COMMAND_SEP)[1], default=1)

    if (user := User.get_or_none(id=query.from_user.id)) is None:
        await update.message.reply_text(ONLY_REGISTERED_USER_ALLOWED)
        return

    text, reply_markup = my_ongoing_positions(user, page, POSITION_PER_PAGE)

    try:
        await query.edit_message_text(text, ParseMode.MARKDOWN_V2, reply_markup=reply_markup, disable_web_page_preview=True)
    except error.BadRequest:
        await query.answer(NOTHING_CHANGED)

async def my_expired_positions_inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    page = parse_int(query.data.split(COMMAND_SEP)[1], default=1)

    if (user := User.get_or_none(id=query.from_user.id)) is None:
        await query.edit_message_text(ONLY_REGISTERED_USER_ALLOWED, ParseMode.MARKDOWN_V2, reply_markup=None)
        return

    text, reply_markup = my_expired_positions(user, page, POSITION_PER_PAGE)

    try:
        await query.edit_message_text(text, ParseMode.MARKDOWN_V2, reply_markup=reply_markup, disable_web_page_preview=True)
    except error.BadRequest:
        await query.answer(NOTHING_CHANGED)

async def removed_positions_inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    page = parse_int(query.data.split(COMMAND_SEP)[1], default=1)

    if (user := User.get_or_none(id=query.from_user.id)) is None or not user.is_admin:
        await query.edit_message_text(ONLY_ADMINS_ALLOWED, ParseMode.MARKDOWN_V2, reply_markup=None)
        return

    text, reply_markup = removed_positions(user, page, POSITION_PER_PAGE)

    try:
        await query.edit_message_text(text, ParseMode.MARKDOWN_V2, reply_markup=reply_markup, disable_web_page_preview=True)
    except error.BadRequest:
        await query.answer(NOTHING_CHANGED)

async def weekly_reminder_inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    page = parse_int(query.data.split(COMMAND_SEP)[1], default=1)

    if (user := User.get_or_none(id=query.from_user.id)) is None:
        await query.edit_message_text(ONLY_REGISTERED_USER_ALLOWED, reply_markup=None)
        return

    text, reply_markup = upcoming_week_positions(user, page, POSITION_PER_PAGE)

    try:
        await query.edit_message_text(text, ParseMode.MARKDOWN_V2, reply_markup=reply_markup, disable_web_page_preview=True)
    except error.BadRequest:
        await query.answer(NOTHING_CHANGED)

async def daily_reminder_inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    page = parse_int(query.data.split(COMMAND_SEP)[1], default=1)

    if (user := User.get_or_none(id=query.from_user.id)) is None:
        await query.edit_message_text(ONLY_REGISTERED_USER_ALLOWED, reply_markup=None)
        return

    text, reply_markup = upcoming_day_positions(user, page, POSITION_PER_PAGE)

    try:
        await query.edit_message_text(text, ParseMode.MARKDOWN_V2, reply_markup=reply_markup, disable_web_page_preview=True)
    except error.BadRequest:
        await query.answer(NOTHING_CHANGED)

async def inline_university_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    button = InlineQueryResultsButton('↩ Back to the bot', start_parameter='start')

    results = []

    logger.info(query)

    if User.get_or_none(id=update.effective_user.id) is not None:
        if not query:
            return
        else:
            for uni in University.search(query):
                results.append(InlineQueryResultArticle(id=str(uni.id), title=uni.name, description=f"Rank: {uni.usn_rank} ({uni.usn_cs_rank} in CS)",
                                                        input_message_content=InputTextMessageContent(f"/{UNIVERSITY_POSITIONS_COMMAND}{uni.id}", parse_mode=ParseMode.HTML)))
    else:
        results.append(InlineQueryResultArticle(id='0', title='Registration is needed for accessing the bot.', input_message_content=InputTextMessageContent('@phd_finder_bot')))

    await update.inline_query.answer(results, button=button)


def main() -> None:
    application = Application.builder().token(TG_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", welcome_command_handler))

    application.add_handler(MessageHandler(filters.Regex(fr'/{WATCH_COMMAND}'), watch_position_command_handler))
    application.add_handler(MessageHandler(filters.Regex(fr'/{UNWATCH_COMMAND}'), unwatch_position_command_handler))
    application.add_handler(MessageHandler(filters.Regex(fr'/{RESTORE_COMMAND}'), restore_position_command_handler))
    application.add_handler(MessageHandler(filters.Regex(fr'/{UNIVERSITY_POSITIONS_COMMAND}'), university_positions_intro_command_handler))

    application.add_handler(MessageHandler(filters.Text(UNIVERSITIES_COMMAND), universities_intro_command_handler))
    application.add_handler(MessageHandler(filters.Text(ONGOING_POSITIONS_COMMAND), my_ongoing_positions_intro_command_handler))
    application.add_handler(MessageHandler(filters.Text(EXPIRED_POSITIONS_COMMAND), my_expired_positions_intro_command_handler))
    application.add_handler(MessageHandler(filters.Text(REMOVED_POSITIONS_COMMAND), removed_positions_intro_command_handler))

    application.add_handler(CallbackQueryHandler(watch_channel_position_inline_handler, WATCH_CHANNEL_POSITION_INLINE))
    application.add_handler(CallbackQueryHandler(remove_channel_position_inline_handler, REMOVE_CHANNEL_POSITION_INLINE))

    application.add_handler(CallbackQueryHandler(university_positions_inline_handler, UNIVERSITY_POSITIONS_INLINE))
    application.add_handler(CallbackQueryHandler(universities_inline_handler, UNIVERSITIES_INLINE))
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

    application.add_handler(InlineQueryHandler(inline_university_query_handler))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
