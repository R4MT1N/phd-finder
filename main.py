import argparse
import asyncio
from typing import List, Type

from lib import University
from models import University as MUniversity
from models.tables import User, create_tables, drop_tables
from universities import *
from scheduler import *
from datetime import datetime, timedelta
from random import randint
from dotenv import load_dotenv
from pathlib import Path


university_classes: List[Type[University]] = [KULeuven, Maastricht, Radboud, Twente, Vrije, Erasmus, Groningen, Leiden, Eindhoven,
                                              Utrecht, Amsterdam, Delft, Umea, Lulea, Linkoping, Gothenburg, Lund, KTH, Uppsala,
                                              Stockholm, Chalmers]

def seed_db():
    class_mapper = {}
    for university_class in university_classes:
        class_mapper[university_class.Name] = university_class
        university_class().create_db_record()

    return class_mapper

def initialize_db():
    create_tables()
    seed_db()
    print("Initialization is successfully done.")

def find_new_positions(full_mode=False):
    class_mapper = seed_db()
    new_positions = 0

    for university in MUniversity.select():
        if full_mode or (university.next_check_at is None or university.next_check_at > datetime.now()):
            university_instance = class_mapper[university.name]()
            university_instance.fetch_positions()
            university.next_check_at = datetime.now() + timedelta(hours=randint(3, 6), minutes=randint(0, 5) * 10)
            university.save()
            new_positions += university_instance.total_new_positions

    print(f"{new_positions} new positions were found and added to database.")

def setup():
    initialize_db()
    find_new_positions(True)


load_dotenv(Path(__file__).parent.joinpath('.env'), override=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='PhD Finder', description='I find PhD positions from a set of universities.')
    subparsers = parser.add_subparsers(dest='command')

    parser_0 = subparsers.add_parser('setup', help='Initialize the program including generating database tables')

    parser_1 = subparsers.add_parser('reset-factory', help='Removes all the data and setup again')

    parser_2 = subparsers.add_parser('check', help='Check for new position announcements')
    parser_2.add_argument('--type', choices=['normal', 'full'], default='normal')

    parser_3 = subparsers.add_parser('register-user', help='Register a normal user')
    parser_3.add_argument('user_id', action='store', type=int, help='Telegram user id')

    parser_4 = subparsers.add_parser('register-admin', help='Register a user as admin')
    parser_4.add_argument('user_id', action='store', type=int, help='Telegram user id')

    parser_5 = subparsers.add_parser('remove-user', help='Remove user')
    parser_5.add_argument('user_id', action='store', type=int, help='Telegram user id')

    parser_6 = subparsers.add_parser('notify', help='Notify positions')

    parser_7 = subparsers.add_parser('remind', help='Remind upcoming deadlines')
    parser_7.add_argument('--type', choices=['day', 'week', 'month'], default='new')

    parser_8 = subparsers.add_parser('prune', help='Remove expired telegram messages')

    args = parser.parse_args()

    if args.command == 'setup':
        setup()

    elif args.command == 'reset-factory':
        drop_tables()
        print('Tables dropped.')
        setup()

    elif args.command == 'register-user':
        user, is_created = User.get_or_create(id=args.user_id)

        if is_created:
            print(f"User '{user.id}' is successfully registered.")
        else:
            print(f"User '{user.id}' is already registered.")

    elif args.command == 'register-admin':
        user, is_created = User.get_or_create(id=args.user_id, defaults={'is_admin': True})

        if is_created:
            print(f"Admin '{user.id}' is successfully registered.")
        else:
            print(f"Admin '{user.id}' already exist.")

    elif args.command == 'remove-user':
        if user := User.get_or_none(id=args.user_id):
            user.delete_instance()
            print(f"User '{args.user_id}' is removed.")
        else:
            print(f"User '{args.user_id}' does not exists.")

    elif args.command == 'check':
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
