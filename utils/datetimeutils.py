import datetime


def delta_seconds(date1: datetime.datetime, date2: datetime.datetime):
    return (date1 - date2).total_seconds()
