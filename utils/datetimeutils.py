import datetime

from django.utils import timezone


def delta_seconds(date1: datetime.datetime, date2: datetime.datetime):
    return (date1 - date2).total_seconds()


def now_datetime():
    return datetime.datetime.now(timezone.get_current_timezone())


def from_timestamp(timestamp):
    return datetime.datetime.fromtimestamp(timestamp, tz=timezone.get_current_timezone())
