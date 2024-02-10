import os
import time
from pathlib import Path
from dotenv import load_dotenv
from telegram import Bot, error
from tgbot import publish_position, constants
from models.tables import Position, Message

load_dotenv(Path(__file__).parent.joinpath('.env'), override=True)

async def notify_new_positions():
    positions = list(Position.news(per_page=10))

    if not positions:
        print("No new position were found.")
        return

    bot = Bot(constants.TG_BOT_TOKEN)
    await bot.initialize()

    for position in positions:
        await publish_position(bot, constants.CHANNEL_CHAT_ID, position)
        time.sleep(1)

async def remove_expired_messages():
    expired_messages = list(Message.expired_messages())

    if not expired_messages:
        print("No expired messages exist.")
        return

    bot = Bot(constants.TG_BOT_TOKEN)
    await bot.initialize()

    for message in expired_messages:
        try:
            await bot.delete_message(message.user.chat_id, message.id)
        except error.BadRequest:
            pass

        message.delete_instance()
