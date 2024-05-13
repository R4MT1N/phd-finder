import logging
import time
from telegram import Bot, error
from telegram.constants import ParseMode
from tgbot.helpers import generate_position_list, notify_admin
from models.tables import Position, Message, User
from tgbot import publish_position
from tgbot.constants import *

logging.basicConfig()
logger = logging.getLogger('scheduler')
logger.setLevel(logging.INFO)


async def notify_new_positions():
    positions = list(Position.news().paginate(1, 10))

    if not positions:
        logger.info("No new position were found.")
        return

    bot = Bot(TG_BOT_TOKEN)
    await bot.initialize()

    for position in positions:
        await publish_position(bot, CHANNEL_CHAT_ID, position)
        time.sleep(1)

async def remove_expired_messages():
    expired_messages = list(Message.expired_messages())

    if not expired_messages:
        logger.info("No expired messages exist.")
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

        text, reply_markup = generate_position_list(user, query, UPCOMING_WEEK_DEADLINES_TITLE, 1, 5, total, UPCOMING_WEEK_DEADLINES_INLINE)
        await bot.send_message(user.chat_id, text, ParseMode.MARKDOWN_V2, reply_markup=reply_markup, disable_web_page_preview=True)

    info_text = 'Upcoming week deadlines just announced!'
    logger.info(info_text)
    await notify_admin(info_text)


async def remind_daily_deadlines():
    bot = Bot(TG_BOT_TOKEN)

    for user in User.select():
        query = user.upcoming_deadlines(days=1)

        if (total := query.count()) == 0:
            continue

        text, reply_markup = generate_position_list(user, query, UPCOMING_DAY_DEADLINES_TITLE, 1, 5, total, UPCOMING_DAY_DEADLINES_INLINE)

        await bot.initialize()
        await bot.send_message(user.chat_id, text, ParseMode.MARKDOWN_V2, reply_markup=reply_markup, disable_web_page_preview=True)

    info_text = 'Upcoming day deadlines just announced!'
    logger.info(info_text)
    await notify_admin(info_text)
