from peewee import Query
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.constants import ParseMode
from tgbot.constants import *
from math import ceil
from models import Position, Message


def pagination_reply_markup(page, total_pages, inline_command):
    keyboard = [[]]

    if page > 1:
        keyboard[0].append(
            InlineKeyboardButton(PREVIOUS_BTN, callback_data=f'{inline_command}{COMMAND_SEP}{page - 1}'))

    keyboard[0].append(InlineKeyboardButton(REFRESH_BTN, callback_data=f'{inline_command}{COMMAND_SEP}1'))

    if page < total_pages:
        keyboard[0].append(
            InlineKeyboardButton(NEXT_BTN, callback_data=f'{inline_command}{COMMAND_SEP}{page + 1}'))

    return InlineKeyboardMarkup(keyboard) if keyboard[0] else None

def resolve_page(page: str) -> int:
    if (page is None) or (not page.isdigit()):
        page = 1
    else:
        page = int(page)

    return page

def format_ongoing_position(index, position):
    lines = [f"*{index}.* [{position.title}]({position.link})", f"{position.university.name} / {position.persian_end_date()}",
             f"➖ /{UNWATCH_COMMAND}{position.id}"]
    return '\n'.join(lines)

def format_removed_position(index, position):
    lines = [f"*{index}.* [{position.title}]({position.link})", f"{position.university.name} / {position.persian_end_date()}",
             f"🔛 /{RESTORE_COMMAND}{position.id}"]
    return '\n'.join(lines)

def format_channel_position(position):
    lines = [f"🎓 *Title*: {position.title}", f"🔗 [Details]({position.link})",
             f"🏫 *Employer*: {position.university.name} ({position.university.country})",
             f"⏰ *Deadline*: {position.persian_end_date()}"]
    return '\n'.join(lines)

async def remove_message(query: CallbackQuery, user):
    await query.message.delete()
    Message.remove(user, query.message.id)

async def publish_position(bot: Bot, chat_id, position, silent=False):
    message = format_channel_position(position)

    keyboard = [
        [InlineKeyboardButton(WATCH_BTN, callback_data=f"{WATCH_CHANNEL_POSITION_INLINE}{COMMAND_SEP}{position.id}"),
         InlineKeyboardButton(REMOVE_BTN, callback_data=f"{REMOVE_CHANNEL_POSITION_INLINE}{COMMAND_SEP}{position.id}")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await bot.send_message(chat_id, message, ParseMode.MARKDOWN, disable_web_page_preview=True, reply_markup=reply_markup, disable_notification=silent)
        position.publish()
    except:
        pass

def generate_position_list(query: Query, title: str, page: int, per_page: int, total: int, paging_inline_command):
    total_pages = ceil(total / per_page)
    page = min(total_pages, page)

    lines = [
        f"*{title}* - {(page - 1) * per_page + 1} to {min(total, page * per_page)} from {total}"]

    for index, position in enumerate(query.paginate(page, per_page)):
        lines += [f"\n{format_ongoing_position(per_page * (page - 1) + index + 1, position)}"]

    text = '\n'.join(lines)
    reply_markup = pagination_reply_markup(page, total_pages, paging_inline_command)

    return text, reply_markup

def my_ongoing_positions(user, page, per_page):
    query = user.ongoing_positions()

    if (total_num := query.count()) == 0:
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(REFRESH_BTN, callback_data=f'{MY_ONGOING_POSITIONS_INLINE}{COMMAND_SEP}1')]])
        text = 'No ongoing position is in watchlist.'
        return text, reply_markup
    else:
        return generate_position_list(query, 'Ongoing Positions', page, per_page, total_num, MY_ONGOING_POSITIONS_INLINE)

def my_expired_positions(user, page, per_page):
    query = user.expired_positions()

    if (total_num := query.count()) == 0:
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(REFRESH_BTN, callback_data=f'{MY_EXPIRED_POSITIONS_INLINE}{COMMAND_SEP}1')]])
        text = 'No expired position is in watchlist.'
        return text, reply_markup
    else:
        return generate_position_list(query, 'Expired Positions', page, per_page, total_num, MY_EXPIRED_POSITIONS_INLINE)

def removed_positions(page, per_page, total_num):
    query = Position.removed()

    if (total_num := query.count()) == 0:
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(REFRESH_BTN, callback_data=f'{REMOVED_POSITIONS_INLINE}{COMMAND_SEP}1')]])
        text = 'No removed position were found.'
        return text, reply_markup
    else:
        return generate_position_list(query, 'Removed Positions', page, per_page, total_num, REMOVED_POSITIONS_INLINE)

def upcoming_week_positions(user, page, per_page):
    query = user.upcoming_deadlines(weeks=1)

    if (total_num := query.count()) == 0:
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(REFRESH_BTN, callback_data=f'{UPCOMING_WEEK_DEADLINES_INLINE}{COMMAND_SEP}1')]])
        text = EMPTY_UPCOMING_WEEK_DEADLINES
        return text, reply_markup
    else:
        return generate_position_list(query, UPCOMING_WEEK_DEADLINES, page, per_page, total_num, UPCOMING_WEEK_DEADLINES_INLINE)

def upcoming_day_positions(user, page, per_page):
    query = user.upcoming_deadlines(days=1)

    if (total_num := query.count()) == 0:
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(REFRESH_BTN, callback_data=f'{UPCOMING_DAY_DEADLINES_INLINE}{COMMAND_SEP}1')]])
        text = EMPTY_UPCOMING_DAY_DEADLINES
        return text, reply_markup
    else:
        return generate_position_list(query, UPCOMING_DAY_DEADLINES, page, per_page, total_num, UPCOMING_DAY_DEADLINES_INLINE)
