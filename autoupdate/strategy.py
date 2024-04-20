import datetime
import time

from api.models import *
from api.settings import Settings as SettingsHighLevel, Timestamps as TimestampsHighLevel
from core.vstulib import VSTULibrary
from core import dto

LIBRARY = VSTULibrary()
SETTINGS = SettingsHighLevel()
TIMESTAMPS = TimestampsHighLevel()

SLEEP_BATCH_TIME = 120


def calculate_next_update():
    pass

def calculate_next_global_update():
    pass


def schedule_short_task(author: Author):
    ShortUpdateTasks.objects.get_or_create(author=author)
    if ShortUpdateTasks.objects.count() >= SETTINGS.max_short_tasks or (calculate_next_global_update() - datetime.datetime.now()).seconds <= SETTINGS.obsolescence_time_seconds:
        return False
    if not ShortUpdateTasks.objects.filter(author=author).exists():
        ShortUpdateTasks.objects.create(author=author)


# Секция кода, которая требует вызова только в сервере автообновления! Нельзя вызывать эти функции в коде бэкенда
def _autoupdate_author(author: Author):
    library_publications = set(map(lambda x: x.info, LIBRARY.search_by_author(dto.Author(author.library_primary_name))))
    local_publications = set(map(lambda x: x.html_content, Publication.objects.filter(author=author)))
    new_publications = library_publications - local_publications
    removed_publications = local_publications - library_publications
    for new in new_publications:
        pub = Publication.objects.create(html_content=new)
        pub.authors.add(author)
        pub.save()
    for old in removed_publications:
        Publication.objects.filter(text=old).delete()


def _autoupdate_author_by_department(author: Author, dep: Department):
    library_publications = set(map(lambda x: x.info, LIBRARY.search_by_author(dto.Author(author.library_primary_name), dto.Department(dep.name, dep.library_id))))
    local_publications = Publication.objects.filter(author=author)
    for pub in local_publications:
        if pub.html_content in library_publications:
            pub.department = dep
            pub.save()
            library_publications.pop(pub.html_content)
    for new in library_publications:
        pub = Publication.objects.create(html_content=new)
        pub.authors.add(author)
        pub.save()


def autoupdate_author(author: Author):
    _autoupdate_author(author)
    _autoupdate_author_by_department(author, author.department)


def short_task_batch():
    pass


def global_autoupdate():
    ShortUpdateTasks.objects.all().delete()
    obsolescence_time = SETTINGS.obsolescence_time_seconds
    batch_size = SETTINGS.request_batch_size
    for i, author in enumerate(Author.objects.all()):
        if not author.last_updated or (datetime.datetime.now() - author.last_updated).seconds < obsolescence_time:
            return
        autoupdate_author(author)
        author.last_updated = datetime.datetime.now()
        author.save()
        if i % batch_size == 0:
            time.sleep(SLEEP_BATCH_TIME)
    TIMESTAMPS.register_global_update()