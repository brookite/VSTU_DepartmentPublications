import datetime
import logging
import time
from croniter import croniter

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

logger = logging.getLogger("autoupdate")


def calculate_next_update():
    last_update = TIMESTAMPS.last_short_update
    global_update_time = calculate_next_global_update()
    if ShortUpdateTasks.objects.count() > 0:
        if datetime.datetime.now() <= last_update + datetime.timedelta(
            seconds=SETTINGS.short_task_batch_update_delay
        ):
            next_update_time = last_update + datetime.timedelta(
                seconds=SETTINGS.short_task_batch_update_delay
            )
        else:
            next_update_time = datetime.datetime.now() + datetime.timedelta(
                seconds=SETTINGS.short_tasks_check_interval
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
    return croniter(SETTINGS.cron_schedule, datetime.datetime.now()).get_next(
        datetime.datetime
    )


def schedule_short_task(author: Author):
    if (
        delta_seconds(calculate_next_global_update(), datetime.datetime.now())
        <= SETTINGS.obsolescence_time_seconds
    ):
        logger.debug(
            f"Одиночная задача не была создана, в скором времени произойдет глобальное обновление {calculate_next_global_update()}"
        )
        return False
    ShortUpdateTasks.objects.get_or_create(author=author)
    logger.info("Добавлена новая одиночная задача")
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
    logger.debug(
        f"Найдено {new_publications} новых публикаций, удалению подлежит {removed_publications} публикаций"
    )
    for new in new_publications:
        pub = Publication.objects.create(html_content=new)
        pub.authors.add(author)
        pub.save()
    for old in removed_publications:
        logger.debug(f"Удаление публикации: {old}")
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
    logger.debug(f"Обновление автора {author.library_primary_name} [{author.pk}]")
    _autoupdate_author(author)
    logger.debug(
        f"Обновление автора {author.library_primary_name} [{author.pk}] по кафедре {author.department.name}"
    )
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
        logger.debug(
            f"{global_update_time} будет глобальное автообновление, не выполняю одиночные задачи"
        )
        return
    if datetime.datetime.now() <= last_update + datetime.timedelta(
        seconds=SETTINGS.short_task_batch_update_delay
    ):
        logger.debug(
            "Недавно было выполнение одиночных задач. Ожидание истечения таймаута"
        )
        return
    tasks = ShortUpdateTasks.objects.all()
    tasks = tasks[: min(SETTINGS.max_short_tasks, len(tasks))]
    logger.info(f"Обработка {len(tasks)} одиночных задач начата")
    batch_size = SETTINGS.request_batch_size
    for i, task in enumerate(tasks):
        autoupdate_author(task.author)
        task.delete()
        if i % batch_size == 0:
            time.sleep(SLEEP_BATCH_TIME)
    TIMESTAMPS.register_short_update()
    logger.info(f"Обработка {len(tasks)} одиночных задач завершена")


def global_autoupdate():
    logger.info("Начато глобальное автообновление. Чистка очереди одиночных задач...")
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
        try:
            autoupdate_author(author)
            author.last_updated = datetime.datetime.now()
            author.save()
        except Exception as e:
            logger.error(
                f"Неизвестная ошибка при обновлении автора {author.library_primary_name}, {author.pk}",
                exc_info=True,
            )
        if i % batch_size == 0:
            time.sleep(SLEEP_BATCH_TIME)
    TIMESTAMPS.register_global_update()
    logger.info(f"Глобальное автообновление завершено. Обработано {i + 1} авторов")
