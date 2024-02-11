from __future__ import annotations
from datetime import datetime, timedelta
import jdatetime
from dateutil.relativedelta import relativedelta
from peewee import Query
from playhouse.signals import Model as PModel
from peewee import *
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent.joinpath('.env'), override=True)

db = PostgresqlDatabase(os.getenv('POSTGRES_DB'), user=os.getenv('POSTGRES_USER'),
                        password=os.getenv('POSTGRES_PASSWORD'), host=os.getenv('POSTGRES_HOST'),
                        port=os.getenv('POSTGRES_PORT'))


ThroughDeferred1 = DeferredThroughModel()

class BaseModel(PModel):
    class Meta:
        database = db

    def refresh(self):
        return type(self).get(self._pk_expr())

class Country(BaseModel):
    name = CharField(max_length=100, unique=True, primary_key=True)
    created_at: datetime = DateTimeField(default=datetime.now)

    class Meta:
        db_table = 'countries'

class University(BaseModel):
    name = CharField(max_length=100, unique=True, primary_key=True)
    country = ForeignKeyField(Country, backref='universities')
    vacancy_link = CharField(max_length=250)
    usn_rank = IntegerField(null=True)
    usn_cs_rank = IntegerField(null=True)
    qsn_rank = IntegerField(null=True)
    next_check_at: datetime = DateTimeField(null=True)
    created_at: datetime = DateTimeField(default=datetime.now)

    class Meta:
        db_table = 'universities'

class User(BaseModel):
    id = BigIntegerField(primary_key=True)
    is_admin = BooleanField(default=False)
    chat_id = BigIntegerField(null=True)
    created_at: datetime = DateTimeField(default=datetime.now)

    class Meta:
        db_table = 'users'

    def unwatch_position(self, position: Position):
        UserPosition.delete().where((UserPosition.user == self) & (UserPosition.position == position)).execute()

    def ongoing_positions(self) -> Query:
        return Position.select().join(UserPosition).join(User).where((User.id == self.id) & (Position.removed_at.is_null(True)) & (Position.end_date >= datetime.now())).order_by(Position.end_date.asc())

    def expired_positions(self) -> Query:
        return Position.select().join(UserPosition).join(User).where((User.id == self.id) & (Position.removed_at.is_null(True)) & (Position.end_date < datetime.now())).order_by(Position.end_date.asc())

    def upcoming_deadlines(self, days=1, weeks=0, months=0) -> Query:
        rel_delta = relativedelta(days=days, weeks=weeks, months=months)

        return Position.select(Position) \
            .join(UserPosition) \
            .where((UserPosition.user == self) & (Position.removed_at.is_null(True)) & (Position.end_date >= datetime.now()) & (
                    Position.end_date <= datetime.now() + rel_delta)).order_by(Position.end_date.asc())

    def update_chat_id(self, chat_id, save=True):
        self.chat_id = chat_id
        if save:
            self.save()
        return self


class Position(BaseModel):
    PER_PAGE = 5

    id = AutoField()
    university: University = ForeignKeyField(University, backref='positions', on_delete='Cascade', on_update='Cascade')
    title = CharField(max_length=250)
    link = CharField(max_length=250)
    end_date = DateField(null=True)
    start_date = DateField(null=True)
    published_at = DateTimeField(null=True)
    removed_at = DateTimeField(null=True)
    created_at: datetime = DateTimeField(default=datetime.now)
    users = ManyToManyField(User, backref='positions', through_model=ThroughDeferred1)

    class Meta:
        db_table = 'positions'

    def persian_end_date(self):
        return str(jdatetime.date.fromgregorian(date=self.end_date))

    def remove(self, save=True):
        self.removed_at = datetime.now()
        self.published_at = None
        if save:
            self.save()
        return self

    def publish(self, save=True):
        self.published_at = datetime.now()
        if save:
            self.save()

        return self

    def restore(self, save=True):
        self.removed_at = None
        if save:
            self.save()
        return self

    @classmethod
    def removed(cls) -> Query:
        return cls.select().where(cls.removed_at.is_null(False)).order_by(cls.end_date.asc())

    @classmethod
    def near_deadlines(cls, rel_time):
        return Position.select().where((Position.removed_at.is_null(True)) & (Position.end_date >= datetime.now()) & (
                    Position.end_date <= datetime.now() + rel_time)).order_by(Position.end_date.asc())

    @classmethod
    def news(cls, page=1, per_page=None):
        return Position.select().where((cls.published_at.is_null(True)) & (cls.removed_at.is_null(True))).order_by(cls.end_date.asc()).paginate(page, per_page or cls.PER_PAGE)


class UserPosition(BaseModel):
    user = ForeignKeyField(User, on_delete='Cascade', on_update='Cascade')
    position = ForeignKeyField(Position, on_delete='Cascade', on_update='Cascade')
    created_at: datetime = DateTimeField(default=datetime.now, index=True)

    class Meta:
        primary_key = CompositeKey('user', 'position')
        db_table = 'user_positions'


class Message(BaseModel):
    id = BigIntegerField()
    user = ForeignKeyField(User, backref='messages', on_delete='Cascade', on_update='Cascade')
    expire_at = DateTimeField(null=True, index=True)

    class Meta:
        db_table = 'messages'

    @classmethod
    def expired_messages(cls):
        return cls.select().where(cls.expire_at <= datetime.now())

    @staticmethod
    def add(user: User, message_id, expire_in_minutes=1):
        Message.create(user=user, id=message_id, expire_at=datetime.now() + timedelta(minutes=expire_in_minutes))

    @staticmethod
    def remove(user: User, message_id):
        Message.delete().where((Message.user == user) & (Message.id == message_id)).execute()


ThroughDeferred1.set_model(UserPosition)
Position._meta.add_field('users', User.positions)

def create_tables():
    with db:
        db.create_tables([Country, University, Position, User, UserPosition, Message])
