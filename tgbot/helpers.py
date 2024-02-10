from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.constants import ParseMode
from tgbot.constants import *
from math import ceil
from models import Position, Message

def format_ongoing_position(index, position):
    lines = [f"*{index}.* [{position.title}]({position.link})", f"{position.university.name} - {position.persian_end_date()}",
             f"➖ /{UNWATCH_COMMAND}{position.id}"]
    return '\n'.join(lines)

def format_removed_position(index, position):
    lines = [f"*{index}.* [{position.title}]({position.link})", f"{position.university.name} - {position.persian_end_date()}",
             f"🔛 /{RESTORE_COMMAND}{position.id}"]
    return '\n'.join(lines)

def format_channel_position(position):
    lines = [f"🎓 *Title*: {position.title}", f"🔗 [Link]({position.link})",
             f"🏫 *Employer*: {position.university.name} ({position.university.country})",
             f"⏰ *Deadline*: {position.persian_end_date()}"]
    return '\n'.join(lines)

async def remove_message(query: CallbackQuery, user):
    await query.message.delete()
    Message.remove(user, query.message.id)

async def send_single_position(bot: Bot, chat_id, position, silent=False):
    message = format_channel_position(position)

    keyboard = [
        [InlineKeyboardButton("➕ Watch", callback_data=f"{WATCH_CHANNEL_POSITION_INLINE}+{position.id}"),
         InlineKeyboardButton("❌ Remove", callback_data=f"{REMOVE_CHANNEL_POSITION_INLINE}+{position.id}")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await bot.send_message(chat_id, message, ParseMode.MARKDOWN, disable_web_page_preview=True, reply_markup=reply_markup, disable_notification=silent)
        position.publish()
    except:
        pass

async def publish_position(bot: Bot, chat_id, position, silent=False):
    await send_single_position(bot, chat_id, position, silent)
    ...

def my_ongoing_positions(user, page: str, per_page, total_num):
    total_pages = ceil(total_num / per_page)

    if (page is None) or (not page.isdigit()) or (int(page) > total_pages):
        page = 1
    else:
        page = int(page)

    lines = [f"*My Ongoing Positions* - {(page - 1) * per_page + 1} to {min(total_num, page * per_page)} from {total_num}"]

    for index, position in enumerate(user.ongoing_positions(page=page, per_page=per_page)):
        lines += [f"\n{format_ongoing_position(per_page * (page - 1) + index + 1, position)}"]

    text = '\n'.join(lines)

    keyboard = [[]]

    if page > 1:
        keyboard[0].append(InlineKeyboardButton("⬅️ Previous", callback_data=f'{MY_ONGOING_POSITIONS_INLINE}+{page - 1}'))

    keyboard[0].append(InlineKeyboardButton("🔄 Refresh", callback_data=f'{MY_ONGOING_POSITIONS_INLINE}+1'))

    if page < total_pages:
        keyboard[0].append(InlineKeyboardButton("➡️ Next", callback_data=f'{MY_ONGOING_POSITIONS_INLINE}+{page + 1}'))

    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard[0] else None

    return text, reply_markup

def removed_positions(user, page: str, per_page, total_num):
    total_pages = ceil(total_num / per_page)

    if (page is None) or (not page.isdigit()) or (int(page) > total_pages):
        page = 1
    else:
        page = int(page)

    lines = [f"*Removed Positions* - {(page - 1) * per_page + 1} to {min(total_num, page * per_page)} from {total_num}"]

    for index, position in enumerate(Position.removed(page=page, per_page=per_page)):
        lines += [f"\n{format_removed_position(per_page * (page - 1) + index + 1, position)}"]

    text = '\n'.join(lines)

    keyboard = [[]]

    if page > 1:
        keyboard[0].append(InlineKeyboardButton("⬅️ Previous", callback_data=f'{REMOVED_POSITIONS_INLINE}+{page - 1}'))

    keyboard[0].append(InlineKeyboardButton("🔄 Refresh", callback_data=f'{REMOVED_POSITIONS_INLINE}+1'))

    if page < total_pages:
        keyboard[0].append(InlineKeyboardButton("➡️ Next", callback_data=f'{REMOVED_POSITIONS_INLINE}+{page + 1}'))

    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard[0] else None

    return text, reply_markup

def my_expired_positions(user, page: str, per_page, total_num):
    total_pages = ceil(total_num / per_page)

    if (page is None) or (not page.isdigit()) or (int(page) > total_pages):
        page = 1
    else:
        page = int(page)

    lines = [f"*My Expired Positions* - {(page - 1) * per_page + 1} to {min(total_num, page * per_page)} from {total_num}"]

    for index, position in enumerate(user.expired_positions(page=page, per_page=per_page)):
        lines += [f"\n{format_ongoing_position(per_page * (page - 1) + index + 1, position)}"]

    text = '\n'.join(lines)

    keyboard = [[]]

    if page > 1:
        keyboard[0].append(InlineKeyboardButton("⬅️ Previous", callback_data=f'{MY_EXPIRED_POSITIONS_INLINE}+{page - 1}'))

    keyboard[0].append(InlineKeyboardButton("🔄 Refresh", callback_data=f'{MY_EXPIRED_POSITIONS_INLINE}+1'))

    if page < total_pages:
        keyboard[0].append(InlineKeyboardButton("➡️ Next", callback_data=f'{MY_EXPIRED_POSITIONS_INLINE}+{page + 1}'))

    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard[0] else None

    return text, reply_markup
