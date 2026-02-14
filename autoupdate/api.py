import datetime
import logging

from apscheduler.triggers.cron import CronTrigger

from api.models import Author, ShortUpdateTasks
from api.settings import Settings as SettingsHighLevel
from api.settings import Timestamps as TimestampsHighLevel
from core.vstulib import VSTULibrary
from utils.datetimeutils import delta_seconds, now_datetime

LIBRARY = VSTULibrary()
_SETTINGS = None
_TIMESTAMPS = None
SLEEP_BATCH_TIME = 120
INFO_UPDATE_SLEEP_TIME = 10
logger = logging.getLogger("autoupdate")


def get_settings():
    global _SETTINGS

    if not _SETTINGS:
        _SETTINGS = SettingsHighLevel()

    return _SETTINGS

def get_timestamps():
    global _TIMESTAMPS

    if not _TIMESTAMPS:
        _TIMESTAMPS = TimestampsHighLevel()

    return _TIMESTAMPS

def calculate_next_update():
    last_update = get_timestamps().last_short_update
    global_update_time = calculate_next_global_update()
    if ShortUpdateTasks.objects.count() > 0:
        if now_datetime() <= last_update + datetime.timedelta(
            seconds=get_settings().short_task_batch_update_delay,
        ):
            next_update_time = last_update + datetime.timedelta(
                seconds=get_settings().short_task_batch_update_delay,
            )
        else:
            next_update_time = now_datetime() + datetime.timedelta(seconds=get_settings().short_tasks_check_interval)
        if (
            abs(delta_seconds(global_update_time, next_update_time))
            < get_settings().obsolescence_time_seconds
        ):
            return global_update_time + datetime.timedelta(
                seconds=get_settings().obsolescence_time_seconds,
            )
        return next_update_time
    return global_update_time


def calculate_next_global_update() -> datetime.datetime:
    return CronTrigger.from_crontab(get_settings().cron_schedule).get_next_fire_time(None, now_datetime()) # type: ignore


def schedule_short_task(author: Author):
    if (
        delta_seconds(
            calculate_next_global_update(),
            now_datetime(),
        )
        <= get_settings().obsolescence_time_seconds
    ):
        logger.debug(
            f"Одиночная задача не была создана, в скором времени произойдет глобальное обновление {calculate_next_global_update()}",
        )
        return False
    ShortUpdateTasks.objects.get_or_create(author=author)
    logger.info("Добавлена новая одиночная задача")
    return True
