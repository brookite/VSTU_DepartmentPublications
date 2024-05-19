import time
from typing import Optional

from api.models import *
from autoupdate.api import *
from core import dto
from utils.datetimeutils import delta_seconds


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
    author: Author, use_alias: Optional[str] = None, allow_removing: bool = False
):
    name = author.library_primary_name if not use_alias else use_alias
    library_publications = set(
        map(
            lambda x: x.info,
            LIBRARY.search_by_author(dto.Author(name))[1],
        )
    )
    local_publications = set(
        map(lambda x: x.html_content, Publication.objects.filter(authors__in=[author]))
    )
    new_publications = library_publications - local_publications
    if allow_removing:
        removed_publications = local_publications - library_publications
    else:
        removed_publications = set()
    logger.debug(
        f"Найдено {len(new_publications)} новых публикаций, удалению подлежит {len(removed_publications)} публикаций"
    )
    for new in new_publications:
        pub, created = Publication.objects.get_or_create(html_content=new)
        pub.authors.add(author)
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


def _autoupdate_author_by_department(
    author: Author, dep: Department, use_alias: Optional[str] = None
):
    name = author.library_primary_name if not use_alias else use_alias
    library_publications = set(
        map(
            lambda x: x.info,
            LIBRARY.search_by_author(
                dto.Author(name),
                dto.Department(
                    dep.name,
                    dep.library_id,
                    dto.Faculty(dep.faculty.name, dep.faculty.library_id),
                ),
            )[1],
        )
    )
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
    for new in library_publications:
        pub, created = Publication.objects.get_or_create(html_content=new)
        pub.authors.add(author)
        pub.save()


def autoupdate_author(author: Author):
    logger.debug(f"Обновление автора {author.library_primary_name} [{author.pk}]")
    _autoupdate_author(author, allow_removing=True)
    logger.debug(
        f"Обновление автора {author.library_primary_name} [{author.pk}] по кафедре {author.department.name}"
    )
    _autoupdate_author_by_department(author, author.department)
    logger.debug(f"Обновление даты обновления {author.library_primary_name}")
    for alias in AuthorAlias.objects.filter(author=author):
        logger.debug(
            f"Обновление автора {author.library_primary_name} по обозначению: {alias.alias}"
        )
        _autoupdate_author(author, alias.alias)
        _autoupdate_author_by_department(author, author.department, alias.alias)
    author.last_updated = datetime.datetime.now().replace(
        tzinfo=timezone.get_current_timezone()
    )
    author.save()


def short_task_batch():
    if Department.objects.count() == 0:
        _update_university_info()
    if ShortUpdateTasks.objects.count() == 0:
        return
    global_update_time = calculate_next_global_update()
    last_update = TIMESTAMPS.last_short_update
    if (
        abs(
            delta_seconds(
                global_update_time,
                datetime.datetime.now().replace(tzinfo=timezone.get_current_timezone()),
            )
        )
        < SETTINGS.obsolescence_time_seconds
    ):
        logger.debug(
            f"{global_update_time} будет/было глобальное автообновление, не выполняю одиночные задачи"
        )
        return
    if datetime.datetime.now().replace(
        tzinfo=timezone.get_current_timezone()
    ) <= last_update + datetime.timedelta(
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


def global_autoupdate(skip_university_update=False):
    logger.info("Начато глобальное автообновление. Чистка очереди одиночных задач...")
    ShortUpdateTasks.objects.all().delete()
    if not skip_university_update:
        _update_university_info()
    obsolescence_time = SETTINGS.obsolescence_time_seconds
    batch_size = SETTINGS.request_batch_size
    i = -1
    for i, author in enumerate(Author.objects.all()):
        if (
            author.last_updated
            and delta_seconds(
                datetime.datetime.now().replace(tzinfo=timezone.get_current_timezone()),
                author.last_updated,
            )
            < obsolescence_time
        ):
            continue
        try:
            autoupdate_author(author)
        except Exception as e:
            logger.error(
                f"Неизвестная ошибка при обновлении автора {author.library_primary_name}, {author.pk}",
                exc_info=True,
            )
        if (i + 1) % batch_size == 0:
            time.sleep(SLEEP_BATCH_TIME)
    TIMESTAMPS.register_global_update()
    logger.info(f"Глобальное автообновление завершено. Обработано {i + 1} авторов")
