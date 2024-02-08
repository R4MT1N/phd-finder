from telegram import Bot, Message
from telegram.constants import ParseMode
from dotenv import load_dotenv
from pathlib import Path
from models.tables import Position
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
import os

load_dotenv(Path(__file__).parent.joinpath('.env'), override=True)


def single_position_markdown(position):
    lines = [f"✍️ {position.title} [(Link)]({position.link})", f"🏫 {position.university.name}", f"⏰ {position.persian_end_date()}"]
    return '\n'.join(lines)

async def notify_new_positions():
    bot = Bot(os.getenv('TG_BOT_TOKEN'))
    chat_id = os.getenv('TG_CHANNEL_ID')

    for position in Position.select().where(Position.telegram_message_id.is_null(True)):
        message = await bot.send_message(chat_id, single_position_markdown(position), ParseMode.MARKDOWN, disable_web_page_preview=True, write_timeout=5, read_timeout=5)
        position.telegram_message_id = message.message_id
        position.save()
        time.sleep(1)

async def notify_current_day_positions():
    lines = []
    for position in Position.select().where((Position.end_date >= datetime.now()) & (Position.end_date <= datetime.now() + relativedelta(days=1))):
        lines += [f"\n{single_position_markdown(position)}"]

    if lines:
        lines.insert(0, "⭐️ *Today Deadlines* ⭐️")

    bot = Bot(os.getenv('TG_BOT_TOKEN'))
    chat_id = os.getenv('TG_CHANNEL_ID')

    await bot.send_message(chat_id, '\n'.join(lines), ParseMode.MARKDOWN, disable_web_page_preview=True)

async def notify_current_week_positions():
    lines = []
    for position in Position.select().where((Position.end_date >= datetime.now()) & (Position.end_date <= datetime.now() + relativedelta(weeks=1))):
        lines += [f"\n{single_position_markdown(position)}"]

    if lines:
        lines.insert(0, "⭐️ *This Week Deadlines* ⭐️")

    bot = Bot(os.getenv('TG_BOT_TOKEN'))
    chat_id = os.getenv('TG_CHANNEL_ID')

    await bot.send_message(chat_id, '\n'.join(lines), ParseMode.MARKDOWN, disable_web_page_preview=True)

async def notify_current_month_positions():
    lines = []
    for position in Position.select().where((Position.end_date >= datetime.now()) & (Position.end_date <= datetime.now() + relativedelta(months=1))):
        lines += [f"\n{single_position_markdown(position)}"]

    if lines:
        lines.insert(0, "⭐️ *This Month Deadlines* ⭐️")

    bot = Bot(os.getenv('TG_BOT_TOKEN'))
    chat_id = os.getenv('TG_CHANNEL_ID')

    await bot.send_message(chat_id, '\n'.join(lines), ParseMode.MARKDOWN, disable_web_page_preview=True)
