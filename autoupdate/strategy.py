import datetime
import time

from api.models import *
from api.settings import (
    Settings as SettingsHighLevel,
    Timestamps as TimestampsHighLevel,
)
from core.vstulib import VSTULibrary
from core import dto
from utils.datetimeutils import delta_seconds

LIBRARY = VSTULibrary()
SETTINGS = SettingsHighLevel()
TIMESTAMPS = TimestampsHighLevel()

SLEEP_BATCH_TIME = 120


def calculate_next_update():
    last_update = TIMESTAMPS.last_short_update
    global_update_time = calculate_next_global_update()
    if ShortUpdateTasks.objects.count() > 0:
        if datetime.datetime.now() <= last_update + datetime.timedelta(
            seconds=SETTINGS.short_task_batch_interval_seconds
        ):
            next_update_time = last_update + datetime.timedelta(
                seconds=SETTINGS.short_task_batch_interval_seconds
            )
        else:
            next_update_time = datetime.datetime.now() + datetime.timedelta(
                seconds=SETTINGS.short_tasks_wait_interval_seconds
            )
        if (
            abs(delta_seconds(global_update_time, next_update_time))
            < SETTINGS.obsolescence_time_seconds
        ):
            return global_update_time + datetime.timedelta(
                seconds=SETTINGS.obsolescence_time_seconds
            )
        return next_update_time
    return global_update_time


def calculate_next_global_update():
    last_global_update = TIMESTAMPS.last_global_update
    if last_global_update is None:
        last_global_update = datetime.datetime.now()
    last_global_update -= datetime.timedelta(days=last_global_update.weekday())
    last_global_update = last_global_update.replace(hour=0, minute=0)
    delta = 0
    interval = SETTINGS.autoupdate_interval
    if interval == "week":
        delta += 3600 * 24 * 7 * SETTINGS.autoupdate_interval_length
        day_of_week = SETTINGS.day_of_autoupdate
        days = [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]
        num = days.index(day_of_week)
        delta += 3600 * 24 * num
    elif interval == "day":
        delta += 3600 * 24 * 7 * SETTINGS.autoupdate_interval_length
    elif interval == "month":
        delta += 3600 * 24 * 30 * 3 * SETTINGS.autoupdate_interval_length
    return last_global_update + datetime.timedelta(days=delta)


def schedule_short_task(author: Author):
    ShortUpdateTasks.objects.get_or_create(author=author)
    if (
        delta_seconds(calculate_next_global_update(), datetime.datetime.now())
        <= SETTINGS.obsolescence_time_seconds
    ):
        return False
    if not ShortUpdateTasks.objects.filter(author=author).exists():
        ShortUpdateTasks.objects.create(author=author)
        return True


# Секция кода, которая требует вызова только в сервере автообновления! Нельзя вызывать эти функции в коде бэкенда
def _autoupdate_author(author: Author):
    library_publications = set(
        map(
            lambda x: x.info,
            LIBRARY.search_by_author(dto.Author(author.library_primary_name)),
        )
    )
    local_publications = set(
        map(lambda x: x.html_content, Publication.objects.filter(author=author))
    )
    new_publications = library_publications - local_publications
    removed_publications = local_publications - library_publications
    for new in new_publications:
        pub = Publication.objects.create(html_content=new)
        pub.authors.add(author)
        pub.save()
    for old in removed_publications:
        Publication.objects.filter(text=old).delete()


def _autoupdate_author_by_department(author: Author, dep: Department):
    library_publications = set(
        map(
            lambda x: x.info,
            LIBRARY.search_by_author(
                dto.Author(author.library_primary_name),
                dto.Department(dep.name, dep.library_id),
            ),
        )
    )
    local_publications = Publication.objects.filter(author=author)
    for pub in local_publications:
        if pub.html_content in library_publications:
            pub.department = dep
            pub.save()
            library_publications.remove(pub.html_content)
    for new in library_publications:
        pub = Publication.objects.create(html_content=new)
        pub.authors.add(author)
        pub.save()


def autoupdate_author(author: Author):
    _autoupdate_author(author)
    _autoupdate_author_by_department(author, author.department)


def short_task_batch():
    if ShortUpdateTasks.objects.count() == 0:
        return
    global_update_time = calculate_next_global_update()
    last_update = TIMESTAMPS.last_short_update
    if (
        delta_seconds(global_update_time, datetime.datetime.now())
        < SETTINGS.obsolescence_time_seconds
    ):
        return
    if datetime.datetime.now() <= last_update + datetime.timedelta(
        seconds=SETTINGS.short_task_batch_interval_seconds
    ):
        return
    tasks = ShortUpdateTasks.objects.all()
    tasks = tasks[: min(SETTINGS.max_short_tasks, len(tasks))]
    batch_size = SETTINGS.request_batch_size
    for i, task in enumerate(tasks):
        autoupdate_author(task.author)
        task.delete()
        if i % batch_size == 0:
            time.sleep(SLEEP_BATCH_TIME)
    TIMESTAMPS.register_short_update()


def global_autoupdate():
    if delta_seconds(calculate_next_global_update(), datetime.datetime.now()) <= 0:
        return
    ShortUpdateTasks.objects.all().delete()
    obsolescence_time = SETTINGS.obsolescence_time_seconds
    batch_size = SETTINGS.request_batch_size
    for i, author in enumerate(Author.objects.all()):
        if (
            not author.last_updated
            or delta_seconds(datetime.datetime.now(), author.last_updated)
            < obsolescence_time
        ):
            return
        autoupdate_author(author)
        author.last_updated = datetime.datetime.now()
        author.save()
        if i % batch_size == 0:
            time.sleep(SLEEP_BATCH_TIME)
    TIMESTAMPS.register_global_update()
