import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from telegram import Bot, error
from telegram.constants import ParseMode

from tgbot.helpers import generate_position_list
from models.tables import Position, Message, User, UserPosition
from tgbot import publish_position
from tgbot.constants import *


async def notify_new_positions():
    positions = list(Position.news(per_page=10))

    if not positions:
        print("No new position were found.")
        return

    bot = Bot(TG_BOT_TOKEN)
    await bot.initialize()

    for position in positions:
        await publish_position(bot, CHANNEL_CHAT_ID, position)
        time.sleep(1)

async def remove_expired_messages():
    expired_messages = list(Message.expired_messages())

    if not expired_messages:
        print("No expired messages exist.")
        return

    bot = Bot(TG_BOT_TOKEN)
    await bot.initialize()

    for message in expired_messages:
        try:
            await bot.delete_message(message.user.chat_id, message.id)
        except error.BadRequest:
            pass

        message.delete_instance()

async def remind_weekly_deadlines():
    bot = Bot(TG_BOT_TOKEN)
    await bot.initialize()

    for user in User.select():
        query = user.upcoming_deadlines(weeks=1)

        if (total := query.count()) == 0:
            continue

        text, reply_markup = generate_position_list(query, UPCOMING_WEEK_DEADLINES, 1, 5, total, UPCOMING_WEEK_DEADLINES_INLINE)
        await bot.send_message(user.chat_id, text, ParseMode.MARKDOWN, reply_markup=reply_markup, disable_web_page_preview=True)

async def remind_daily_deadlines():
    bot = Bot(TG_BOT_TOKEN)

    for user in User.select():
        query = user.upcoming_deadlines(days=1)

        if (total := query.count()) == 0:
            continue

        text, reply_markup = generate_position_list(query, UPCOMING_DAY_DEADLINES, 1, 5, total, UPCOMING_DAY_DEADLINES_INLINE)

        await bot.initialize()
        await bot.send_message(user.chat_id, text, ParseMode.MARKDOWN, reply_markup=reply_markup, disable_web_page_preview=True)
