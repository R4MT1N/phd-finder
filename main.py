import argparse
import asyncio
from typing import List, Type
from universities import *
from lib import University
from scheduler import *
from datetime import datetime, timedelta
from random import randint
from dotenv import load_dotenv
from pathlib import Path


unis: List[Type[University]] = [KULeuven, Maastricht, Radboud, Twente, Vrije, Erasmus, Groningen, Leiden, Eindhoven,
                                Utrecht, Amsterdam, Delft, Umea, Lulea, Linkoping, Gothenburg, Lund, KTH, Uppsala,
                                Stockholm, Chalmers]

load_dotenv(Path(__file__).parent.joinpath('.env'), override=True)

commands = [
    ('--check', 'Check for new positions'),
    ('--notify', 'Notify new positions to the telegram channel'),
    ('--weekly', 'List positions with a deadline during this week'),
    ('--daily', 'List positions with a deadline during this month'),
    ('--monthly', 'List positions with a deadline during this month')
]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='PhD Finder', description='I find PhD positions from a set of universities.')
    for command in commands:
        parser.add_argument(command[0], action='store_true', help=command[1])

    args = parser.parse_args()

    if args.check:
        for uni in unis:
            instant = uni()
            uni_model = instant.model
            if uni_model.next_check_at is None or uni_model.next_check_at > datetime.now():
                instant.fetch_positions()
                uni_model.next_check_at = datetime.now() + timedelta(hours=randint(3, 6), minutes=randint(0, 5) * 10)
                uni_model.save()

    elif args.notify:
        asyncio.get_event_loop().run_until_complete(notify_new_positions())

    elif args.daily:
        asyncio.get_event_loop().run_until_complete(notify_current_day_positions())

    elif args.weekly:
        asyncio.get_event_loop().run_until_complete(notify_current_week_positions())

    elif args.monthly:
        asyncio.get_event_loop().run_until_complete(notify_current_month_positions())
