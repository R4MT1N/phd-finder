import logging
import argparse
import asyncio
from tgbot import constants
from tgbot.helpers import notify_admin
from typing import List, Type
from models import University as MUniversity, CUniversity
from models.tables import User, create_tables, drop_tables
from universities import *
from scheduler import *
from datetime import datetime, timedelta
from random import randint
import traceback
# from dotenv import load_dotenv
# from pathlib import Path
#
# load_dotenv(Path(__file__).parent.parent.joinpath('.env'), override=True)

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

university_classes: List[Type[CUniversity]] = [Hannover, KULeuven, Maastricht, Radboud, Twente, Vrije, Erasmus, Groningen,
                                               Leiden, Eindhoven, Utrecht, Amsterdam, Delft, Umea, Lulea, Linkoping, Gothenburg,
                                               Lund, KTH, Stockholm, Chalmers, Turku, Oulu, Helsinki, Bergen]

# Uppsala crawler is under maintenance


def seed_db():
    for university_class in university_classes:
        university_class().create_db_record()

    User.get_or_create(id=constants.ADMIN_TG_ID, chat_id=constants.ADMIN_TG_ID, is_admin=True)

    print("Database is seeded successfully.")


def initialize_db():
    create_tables()
    seed_db()


async def send_errors_to_admin(errors):
    await notify_admin([f"Error occurred during the collection process with these universities:", ', '.join(errors)])

def find_new_positions(full_mode=False):
    class_mapper = {}
    for university_class in university_classes:
        class_mapper[university_class.Name] = university_class

    new_positions = 0
    errors = []

    for university in MUniversity.select():
        if university.name not in class_mapper:
            continue

        try:
            if full_mode or (university.next_check_at is None or university.next_check_at <= datetime.now()):
                university_instance = class_mapper[university.name]()
                university_instance.fetch_positions()
                university.next_check_at = datetime.now() + timedelta(hours=randint(1, 2), minutes=randint(0, 59))
                university.save()
                new_positions += university_instance.total_new_positions
        except Exception as e:
            logger.error(traceback.format_exc())
            errors.append(university.name)

    if errors:
        asyncio.get_event_loop().run_until_complete(send_errors_to_admin(errors))

    print(f"{new_positions} new positions were found and added to database.")


def setup():
    initialize_db()
    find_new_positions(True)


def register_user(user_id, is_admin=False):
    user, is_created = User.get_or_create(id=user_id)
    user.is_admin = is_admin
    user.save()

    if is_created:
        return f"User '{user.id}' is updated as {'admin' if is_admin else 'normal user'}"
    else:
        return f"User '{user.id}' is registered as {'admin' if is_admin else 'normal user'}"


def remove_user(user_id):
    if user := User.get_or_none(id=user_id):
        user.delete_instance()
        return f"User '{user_id}' is removed."
    else:
        return f"User '{user_id}' does not exists."


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='PhD Finder', description='I find PhD positions from a set of universities.')
    subparsers = parser.add_subparsers(dest='command')

    parser_0 = subparsers.add_parser('setup', help='Initialize the program including generating database tables')

    parser_1 = subparsers.add_parser('reset-factory', help='Removes all the data and setup again')

    parser_2 = subparsers.add_parser('check', help='Check for new position announcements')
    parser_2.add_argument('--type', choices=['normal', 'full'], default='normal')

    parser_3 = subparsers.add_parser('register-user', help='Register a normal user')
    parser_3.add_argument('user_id', action='store', type=int, help='Telegram user id')
    parser_3.add_argument('--is_admin', action='store_true', help='Whether the user should be an admin')

    parser_4 = subparsers.add_parser('remove-user', help='Remove user')
    parser_4.add_argument('user_id', action='store', type=int, help='Telegram user id')

    parser_5 = subparsers.add_parser('notify', help='Notify positions')

    parser_6 = subparsers.add_parser('remind', help='Remind upcoming deadlines')
    parser_6.add_argument('--type', choices=['day', 'week', 'month'], default='new')

    parser_8 = subparsers.add_parser('prune', help='Remove expired telegram messages')

    args = parser.parse_args()

    if args.command == 'setup':
        setup()

    elif args.command == 'reset-factory':
        drop_tables()
        setup()

    elif args.command == 'register-user':
        register_user(args.user_id, args.is_admin)

    elif args.command == 'remove-user':
        remove_user(args.user_id)

    elif args.command == 'check':
        # asyncio.get_event_loop().run_until_complete(find_new_positions(args.type == 'full'))
        find_new_positions(args.type == 'full')

    elif args.command == 'notify':
        asyncio.get_event_loop().run_until_complete(notify_new_positions())

    elif args.command == 'remind':
        if args.type == 'day':
            asyncio.get_event_loop().run_until_complete(remind_daily_deadlines())
        elif args.type == 'week':
            asyncio.get_event_loop().run_until_complete(remind_weekly_deadlines())

    elif args.command == 'prune':
        asyncio.get_event_loop().run_until_complete(remove_expired_messages())
