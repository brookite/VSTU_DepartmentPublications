import datetime
import logging

from croniter import croniter
from django.utils import timezone

from api.models import ShortUpdateTasks, Author
from api.settings import Settings as SettingsHighLevel, Timestamps as TimestampsHighLevel
from core.vstulib import VSTULibrary
from utils.datetimeutils import delta_seconds

LIBRARY = VSTULibrary()
SETTINGS = SettingsHighLevel()
TIMESTAMPS = TimestampsHighLevel()
SLEEP_BATCH_TIME = 120
INFO_UPDATE_SLEEP_TIME = 10
logger = logging.getLogger("autoupdate")


def calculate_next_update():
    last_update = TIMESTAMPS.last_short_update
    global_update_time = calculate_next_global_update()
    if ShortUpdateTasks.objects.count() > 0:
        if datetime.datetime.now().replace(
            tzinfo=timezone.get_current_timezone()
        ) <= last_update + datetime.timedelta(
            seconds=SETTINGS.short_task_batch_update_delay
        ):
            next_update_time = last_update + datetime.timedelta(
                seconds=SETTINGS.short_task_batch_update_delay
            )
        else:
            next_update_time = datetime.datetime.now().replace(
                tzinfo=timezone.get_current_timezone()
            ) + datetime.timedelta(seconds=SETTINGS.short_tasks_check_interval)
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
    return croniter(
        SETTINGS.cron_schedule,
        datetime.datetime.now().replace(tzinfo=timezone.get_current_timezone()),
    ).get_next(datetime.datetime)


def schedule_short_task(author: Author):
    if (
        delta_seconds(
            calculate_next_global_update(),
            datetime.datetime.now().replace(tzinfo=timezone.get_current_timezone()),
        )
        <= SETTINGS.obsolescence_time_seconds
    ):
        logger.debug(
            f"Одиночная задача не была создана, в скором времени произойдет глобальное обновление {calculate_next_global_update()}"
        )
        return False
    ShortUpdateTasks.objects.get_or_create(author=author)
    logger.info("Добавлена новая одиночная задача")
    return True
