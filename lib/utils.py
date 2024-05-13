from urllib.parse import urljoin, unquote
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta


def read_date(value, format):
    return datetime.strptime(value, format).date()

def read_timestamp(value):
    return datetime.fromtimestamp(value).date()

def clean_text(value, is_quoted=False):
    text = value.strip()
    text = re.sub(r'[\s\u200b]+', ' ', text)

    if is_quoted:
        text = unquote(text)
    return text

def join_urls(base, url):
    return urljoin(base, url)

def past_time(minutes=0, hours=0, days=1, weeks=0, months=0, years=0):
    return datetime.now() - relativedelta(minutes=minutes, hours=hours, weeks=weeks, months=months, years=years)