import argparse
import asyncio
from typing import List, Type
from models.tables import User, Message, create_tables
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='PhD Finder', description='I find PhD positions from a set of universities.')
    subparsers = parser.add_subparsers(dest='command')

    parser_0 = subparsers.add_parser('setup', help='Initialize the program including generating database tables')

    parser_1 = subparsers.add_parser('check', help='Check for new position announcements')
    parser_1.add_argument('--type', choices=['normal', 'full'], default='normal')

    parser_2 = subparsers.add_parser('register-user', help='Register a normal user')
    parser_2.add_argument('user_id', action='store', type=int, help='Telegram user id')

    parser_3 = subparsers.add_parser('register-admin', help='Register a user as admin')
    parser_3.add_argument('user_id', action='store', type=int, help='Telegram user id')

    parser_4 = subparsers.add_parser('remove-user', help='Remove user')
    parser_4.add_argument('user_id', action='store', type=int, help='Telegram user id')

    parser_5 = subparsers.add_parser('notify', help='Notify positions')

    parser_6 = subparsers.add_parser('remind', help='Remind upcoming deadlines')
    parser_6.add_argument('--type', choices=['day', 'week', 'month'], default='new')

    parser_7 = subparsers.add_parser('prune', help='Remove expired telegram messages')

    args = parser.parse_args()

    if args.command == 'setup':
        create_tables()
        print("Initialization is successfully done.")

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
        for uni in unis:
            instant = uni()
            uni_model = instant.model
            if (args.type == 'normal' and uni_model.next_check_at is None or uni_model.next_check_at > datetime.now()) or args.type == 'full':
                instant.fetch_positions()
                uni_model.next_check_at = datetime.now() + timedelta(hours=randint(3, 6), minutes=randint(0, 5) * 10)
                uni_model.save()

    elif args.command == 'notify':
        asyncio.get_event_loop().run_until_complete(notify_new_positions())

    elif args.command == 'remind':
        if args.type == 'day':
            asyncio.get_event_loop().run_until_complete(remind_daily_deadlines())
        elif args.type == 'week':
            asyncio.get_event_loop().run_until_complete(remind_weekly_deadlines())

    elif args.command == 'prune':
        asyncio.get_event_loop().run_until_complete(remove_expired_messages())
