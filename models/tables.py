from datetime import datetime, date
import jdatetime
from playhouse.signals import Model as PModel
from peewee import *
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent.joinpath('.env'), override=True)

db = PostgresqlDatabase(os.getenv('POSTGRES_DB'), user=os.getenv('POSTGRES_USER'),
                        password=os.getenv('POSTGRES_PASSWORD'), host=os.getenv('POSTGRES_HOST'),
                        port=os.getenv('POSTGRES_PORT'))


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

class Position(BaseModel):
    id = AutoField()
    university: University = ForeignKeyField(University, backref='positions')
    title = CharField(max_length=250)
    link = CharField(max_length=250)
    end_date: date = DateField(null=True)
    start_date: date = DateField(null=True)
    is_related = BooleanField(default=True)
    telegram_message_id = BigIntegerField(null=True)
    created_at: datetime = DateTimeField(default=datetime.now)

    class Meta:
        db_table = 'positions'

    def persian_end_date(self):
        return str(jdatetime.date.fromgregorian(date=self.end_date))


def create_tables():
    with db:
        db.create_tables([Country, University, Position])
