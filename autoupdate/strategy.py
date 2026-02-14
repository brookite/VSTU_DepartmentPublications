import datetime
import logging
import re
import time

from api.models import Author, AuthorAlias, Department, Faculty, Publication, ShortUpdateTasks
from autoupdate.api import (
    INFO_UPDATE_SLEEP_TIME,
    LIBRARY,
    SLEEP_BATCH_TIME,
    calculate_next_global_update,
    get_settings,
    get_timestamps,
    parse_publ_year,
)
from autoupdate.email import send_update_mail
from core import dto
from utils.datetimeutils import delta_seconds, now_datetime

logger = logging.getLogger("autoupdate")


def _update_university_info():
    logger.info("Обновляю информацию об университете")
    faculties = LIBRARY.get_all_faculties()
    for faculty in faculties:
        if not Faculty.objects.filter(
            name=faculty.name, library_id=faculty.id
        ).exists():
            logger.info(f"Добавляю новый факультет {faculty.name} [{faculty.id}]")
            Faculty.objects.create(name=faculty.name, library_id=faculty.id)
    for faculty in Faculty.objects.all():
        deps = LIBRARY.get_all_departments(
            dto.Faculty(faculty.name, faculty.library_id)
        )
        for dep in deps:
            if not Department.objects.filter(library_id=dep.id).exists():
                logger.info(
                    f"Добавляю новую кафедру {dep.name} [{dep.id}] в {faculty.name} [{faculty.library_id}]"
                )
                Department.objects.create(
                    name=dep.name, library_id=dep.id, faculty=faculty
                )
        time.sleep(INFO_UPDATE_SLEEP_TIME)
    logger.info("Информация об университете обновлена")


def _autoupdate_author(
    author: Author, use_alias: str | None = None, allow_removing: bool = False
):
    name = use_alias or author.library_primary_name
    library_publications = {x.info for x in LIBRARY.search_by_author(dto.Author(name))[1]}
    local_publications = {x.html_content for x in Publication.objects.filter(authors__in=[author])}
    new_publications = library_publications - local_publications
    removed_publications = local_publications - library_publications if allow_removing else set()
    logger.debug(
        f"Найдено {len(new_publications)} новых публикаций, удалению подлежит {len(removed_publications)} публикаций"
    )
    new_publ_objects = set()
    for new in new_publications:
        year = parse_publ_year(new)
        pub, created = Publication.objects.get_or_create(html_content=new, sort_order=year or 0)
        pub.authors.add(author)
        new_publ_objects.add(pub)
        pub.save()
    # Recommended disable removing publications with compatibility with aliases
    for old in removed_publications:
        logger.debug(f"Удаление публикации: {old}")
        publications = Publication.objects.filter(html_content=old)
        for publication in publications:
            if publication.authors.count() > 1:
                publication.authors.remove(author)
            else:
                publication.delete()
    return new_publ_objects


def _autoupdate_author_by_department(
    author: Author, dep: Department, use_alias: str | None = None
):
    name = use_alias or author.library_primary_name
    library_publications = {x.info for x in LIBRARY.search_by_author(
                dto.Author(name),
                dto.Department(
                    dep.name,
                    dep.library_id,
                    dto.Faculty(dep.faculty.name, dep.faculty.library_id),
                ),
            )[1]}
    local_publications = Publication.objects.filter(authors__in=[author])
    stats_paired_count = 0
    for pub in local_publications:
        if pub.html_content in library_publications:
            pub.department = dep
            stats_paired_count += 1
            pub.save()
            library_publications.remove(pub.html_content)
    logger.debug(
        f"Привязано публикаций {stats_paired_count}, на очереди добавление еще {len(library_publications)}"
    )
    new_publ_objects = set()
    for new in library_publications:
        year = parse_publ_year(new)
        pub, created = Publication.objects.get_or_create(html_content=new, sort_order=year or 0)
        pub.authors.add(author)
        new_publ_objects.add(pub)
        pub.save()
    return new_publ_objects


def autoupdate_author(author: Author):
    logger.debug(f"Обновление автора {author.library_primary_name} [{author.pk}]")
    new_publs = set()
    new_publs.update(_autoupdate_author(author, allow_removing=True))
    logger.debug(
        f"Обновление автора {author.library_primary_name} [{author.pk}] по кафедре {author.department.name}"
    )
    new_publs.update(_autoupdate_author_by_department(author, author.department))
    logger.debug(f"Обновление даты обновления {author.library_primary_name}")
    for alias in AuthorAlias.objects.filter(author=author):
        logger.debug(
            f"Обновление автора {author.library_primary_name} по обозначению: {alias.alias}"
        )
        new_publs.update(_autoupdate_author(author, alias.alias))
        new_publs.update(_autoupdate_author_by_department(author, author.department, alias.alias))
    author.last_updated = now_datetime()
    author.save()
    return new_publs


def short_task_batch():
    if Department.objects.count() == 0:
        _update_university_info()
    if ShortUpdateTasks.objects.count() == 0:
        return
    global_update_time = calculate_next_global_update()
    last_update = get_timestamps().last_short_update
    if (
        abs(
            delta_seconds(
                global_update_time,
                now_datetime()
            )
        )
        < get_settings().obsolescence_time_seconds
    ):
        logger.debug(
            f"{global_update_time} будет/было глобальное автообновление, не выполняю одиночные задачи"
        )
        return
    if now_datetime() <= last_update + datetime.timedelta(
        seconds=get_settings().short_task_batch_update_delay
    ):
        logger.debug(
            "Недавно было выполнение одиночных задач. Ожидание истечения таймаута"
        )
        return
    tasks = ShortUpdateTasks.objects.all()
    tasks = tasks[: min(get_settings().max_short_tasks, len(tasks))]
    logger.info(f"Обработка {len(tasks)} одиночных задач начата")
    batch_size = get_settings().request_batch_size
    for i, task in enumerate(tasks):
        autoupdate_author(task.author)
        task.delete()
        if i % batch_size == 0:
            time.sleep(SLEEP_BATCH_TIME)
    get_timestamps().register_short_update()
    logger.info(f"Обработка {len(tasks)} одиночных задач завершена")


def global_autoupdate(skip_university_update=False):
    logger.info("Начато глобальное автообновление. Чистка очереди одиночных задач...")
    ShortUpdateTasks.objects.all().delete()
    if not skip_university_update:
        _update_university_info()
    obsolescence_time = get_settings().obsolescence_time_seconds
    batch_size = get_settings().request_batch_size
    new_publs: set[Publication] = set()
    i = -1
    for i, author in enumerate(Author.objects.all()):
        if (
            author.last_updated
            and delta_seconds(
                now_datetime(),
                author.last_updated,
            )
            < obsolescence_time
        ):
            continue
        try:
            new_publs.update(autoupdate_author(author))
        except Exception:
            logger.error(
                f"Неизвестная ошибка при обновлении автора {author.library_primary_name}, {author.pk}",
                exc_info=True,
            )
        if (i + 1) % batch_size == 0:
            time.sleep(SLEEP_BATCH_TIME)
    get_timestamps().register_global_update()
    send_update_mail(new_publs)
    logger.info(f"Глобальное автообновление завершено. Обработано {i + 1} авторов")
