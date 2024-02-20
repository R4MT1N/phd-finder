from datetime import datetime
import humanize
from peewee import Query, fn
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.constants import ParseMode
from tgbot.constants import *
from math import ceil
from models import Position, Message, User, University


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

def parse_int(value: str, default: int) -> int:
    if (value is None) or (not value.isdigit()):
        value = default
    else:
        value = int(value)

    return value

def fm(*text, sep=' ', italic=False, bold=False, strikethrough=False, link: str = None):
    text = sep.join([str(t) for t in text])
    text = text.replace("-", "\-").replace('.', '\.').replace('(', '\(').replace(')', '\)')

    if bold:
        text = f'*{text}*'

    if italic:
        text = f'_{text}_'

    if strikethrough:
        text = f'~{text}~'

    if link:
        link = link.replace("-", "\-")
        text = f'[{text}]({link})'

    return text

def format_bot_position(user: User, index, position: Position):
    if user.has_watched(position):
        emoji = '🔕'
        command = f'/{UNWATCH_COMMAND}{position.id}'
    else:
        emoji = '🔔'
        command = f'/{WATCH_COMMAND}{position.id}'

    lines = [f"{fm(index, '.', bold=True)} {fm(position.title, link=position.link, strikethrough=position.is_expired())}",
             f"{fm(position.university.name, italic=True)} @ {fm(position.persian_end_date(), italic=True)}",
             f"{emoji} {command}"]

    return '\n'.join(lines)

def format_bot_university(index, university: University):
    lines = [f"{fm(index, '.', bold=True, sep='')} {fm(university.name, bold=True)} {f'/{UNIVERSITY_POSITIONS_COMMAND}{university.id}'}",
             f"{fm(university.country, italic=True)}",
             f"{fm(f'☑️ {university.ongoing_position_count} / 🔇 {university.removed_position_count}', italic=True)}"]

    t_delta = datetime.now() - university.next_check_at

    if t_delta.total_seconds() < 0:
        lines[-1] += " / " + fm(f"🔄 in {humanize.naturaltime(t_delta).replace(' from now', '')}", italic=True)
    else:
        lines[-1] += " / " + fm(f"⚠️ {humanize.naturaltime(t_delta)}", italic=True)

    return '\n'.join(lines)

def format_removed_position(index, position: Position):
    lines = [f"{fm(index, '.', sep='', bold=True)} {fm(position.title, link=position.link, strikethrough=position.is_expired())}",
             f"{fm(position.university.name, italic=True)} / {fm(position.persian_end_date(), italic=True)}",
             f"⤴️ /{RESTORE_COMMAND}{position.id}"]
    return '\n'.join(lines)

def format_channel_position(position: Position):
    lines = [f"🎓 *Title*: {position.title}", f"🔗 [Details]({position.link})",
             f"🏫 *Employer*: {position.university.name} ({position.university.country})",
             f"⏰ *Deadline*: {position.persian_end_date()}"]
    return '\n'.join(lines)

async def remove_message(query: CallbackQuery, user: User):
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

def generate_position_list(user: User, query: Query, title: str, page: int, per_page: int, total: int, paging_inline_command):
    total_pages = ceil(total / per_page)
    page = min(total_pages, page)

    lines = [
        f"*{title}*", f"{(page - 1) * per_page + 1} to {min(total, page * per_page)} from {total}"]

    for index, position in enumerate(query.paginate(page, per_page)):
        lines += [f"\n{format_bot_position(user, per_page * (page - 1) + index + 1, position)}"]

    text = '\n'.join(lines)
    reply_markup = pagination_reply_markup(page, total_pages, paging_inline_command)

    return text, reply_markup

def generate_removed_position_list(user: User, query: Query, title: str, page: int, per_page: int, total: int, paging_inline_command):
    total_pages = ceil(total / per_page)
    page = min(total_pages, page)

    lines = [
        f"*{title}*", f"{(page - 1) * per_page + 1} to {min(total, page * per_page)} from {total}"]

    for index, position in enumerate(query.paginate(page, per_page)):
        lines += [f"\n{format_removed_position(per_page * (page - 1) + index + 1, position)}"]

    text = '\n'.join(lines)
    reply_markup = pagination_reply_markup(page, total_pages, paging_inline_command)

    return text, reply_markup

def generate_university_list(query: Query, title: str, page: int, per_page: int, total: int, paging_inline_command):
    total_pages = ceil(total / per_page)
    page = min(total_pages, page)

    lines = [
        f"*{title}*", f"{(page - 1) * per_page + 1} to {min(total, page * per_page)} from {total}"]

    for index, position in enumerate(query.paginate(page, per_page)):
        lines += [f"\n{format_bot_university(per_page * (page - 1) + index + 1, position)}"]

    text = '\n'.join(lines)
    reply_markup = pagination_reply_markup(page, total_pages, paging_inline_command)

    return text, reply_markup

def university_positions(user: User, university: University, page, per_page):
    query = university.published_positions()

    if (total_num := query.count()) == 0:
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(REFRESH_BTN, callback_data=COMMAND_SEP.join([UNIVERSITY_POSITIONS_INLINE, str(university.id), str(1)]))]])
        text = fm(f'No positions were found in {university.name}.')

        return text, reply_markup
    else:
        return generate_position_list(user, query, f'Positions in {university.name}', page, per_page, total_num, COMMAND_SEP.join([UNIVERSITY_POSITIONS_INLINE, str(university.id)]))

def university_list(page, per_page):
    query = University.select(University, fn.COUNT(Position).filter((Position.end_date > datetime.now()) & (Position.removed_at.is_null(True))).alias('ongoing_position_count'), fn.COUNT(Position).filter(Position.removed_at.is_null(None)).alias('removed_position_count'))\
        .left_outer_join(Position)\
        .order_by(University.next_check_at.asc())\
        .group_by(University)

    if (total_num := query.count()) == 0:
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(REFRESH_BTN, callback_data=UNIVERSITIES_INLINE)]])
        text = fm('No Universities were found.')

        return text, reply_markup
    else:
        return generate_university_list(query, f'Universities', page, per_page, total_num, UNIVERSITIES_INLINE)

def my_ongoing_positions(user: User, page, per_page):
    query = user.ongoing_positions()

    if (total_num := query.count()) == 0:
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(REFRESH_BTN, callback_data=f'{MY_ONGOING_POSITIONS_INLINE}{COMMAND_SEP}1')]])
        text = fm('No ongoing positions are in watchlist.')
        return text, reply_markup
    else:
        return generate_position_list(user, query, ONGOING_POSITIONS_TITLE, page, per_page, total_num, MY_ONGOING_POSITIONS_INLINE)

def my_expired_positions(user: User, page, per_page):
    query = user.expired_positions()

    if (total_num := query.count()) == 0:
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(REFRESH_BTN, callback_data=f'{MY_EXPIRED_POSITIONS_INLINE}{COMMAND_SEP}1')]])
        text = fm('No expired positions are in watchlist.')
        return text, reply_markup
    else:
        return generate_position_list(user, query, EXPIRED_POSITIONS_TITLE, page, per_page, total_num, MY_EXPIRED_POSITIONS_INLINE)

def removed_positions(user, page, per_page):
    query = Position.removed()

    if (total_num := query.count()) == 0:
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(REFRESH_BTN, callback_data=f'{REMOVED_POSITIONS_INLINE}{COMMAND_SEP}1')]])
        text = fm('No removed positions were found.')
        return text, reply_markup
    else:
        return generate_removed_position_list(user, query, REMOVED_POSITIONS_TITLE, page, per_page, total_num, REMOVED_POSITIONS_INLINE)

def upcoming_week_positions(user, page, per_page):
    query = user.upcoming_deadlines(weeks=1)

    if (total_num := query.count()) == 0:
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(REFRESH_BTN, callback_data=f'{UPCOMING_WEEK_DEADLINES_INLINE}{COMMAND_SEP}1')]])
        text = fm(EMPTY_UPCOMING_WEEK_DEADLINES)
        return text, reply_markup
    else:
        return generate_position_list(user, query, UPCOMING_WEEK_DEADLINES_TITLE, page, per_page, total_num, UPCOMING_WEEK_DEADLINES_INLINE)

def upcoming_day_positions(user, page, per_page):
    query = user.upcoming_deadlines(days=1)

    if (total_num := query.count()) == 0:
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(REFRESH_BTN, callback_data=f'{UPCOMING_DAY_DEADLINES_INLINE}{COMMAND_SEP}1')]])
        text = fm(EMPTY_UPCOMING_DAY_DEADLINES)
        return text, reply_markup
    else:
        return generate_position_list(user, query, UPCOMING_DAY_DEADLINES_TITLE, page, per_page, total_num, UPCOMING_DAY_DEADLINES_INLINE)
