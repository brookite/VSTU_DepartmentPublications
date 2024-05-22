from datetime import datetime, timedelta

from django.db.models import Q
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils import dateformat

from api.models import Author, Publication, Department, Tag
from api.settings import Settings
from autoupdate.api import calculate_next_update, calculate_next_global_update
from utils.datetimeutils import now_datetime


def index(request):
    settings = Settings()
    try:
        short_autoupdate = calculate_next_update()
        global_autoupdate = calculate_next_global_update()
    except Exception:
        short_autoupdate, global_autoupdate = None, None
    return render(
        request,
        "index.html",
        {
            "user": request.user,
            "departments": Department.objects.all(),
            "short_autoupdate": short_autoupdate,
            "global_autoupdate": global_autoupdate,
            "reschedule_minutes": settings.reschedule_minutes,
            "short_batch_hour": settings.short_task_batch_update_delay // 3600,
            "short_batch_count": settings.max_short_tasks,
        },
    )


def updates(request):
    settings = Settings()
    try:
        short_autoupdate = calculate_next_update()
        global_autoupdate = calculate_next_global_update()
    except Exception:
        short_autoupdate, global_autoupdate = None, None
    return render(request, "updates.html", {
        "user": request.user,
        "short_autoupdate": short_autoupdate,
        "global_autoupdate": global_autoupdate,
        "reschedule_minutes": settings.reschedule_minutes,
        "short_batch_hour": settings.short_task_batch_update_delay // 3600,
        "short_batch_count": settings.max_short_tasks,
    })


def author_list(request):
    q = request.GET.get("q", "")
    dep_id = request.GET.get("department")
    if dep_id:
        dep_id = int(dep_id)
    else:
        dep_id = None
    tags = request.GET.get("tags", "").split(",")
    if "" in tags:
        tags.remove("")
    filtered_tags = []
    for tag in tags:
        if (tagobj := Tag.objects.filter(name=tag)).exists():
            filtered_tags.append(tagobj.first())
    if q.strip():
        query = Q(full_name__icontains=q) | Q(library_primary_name__icontains=q)
    else:
        query = Q()
    if dep_id:
        query &= Q(department__id=dep_id)
    if len(filtered_tags):
        query &= Q(tag__in=filtered_tags)
    authors = Author.objects.filter(query)[:100]
    return render(request, "people_list.html", {"authors": authors})


def author_details(request):
    author_id = request.GET.get("author_id")
    author = Author.objects.get(id=author_id)
    publications = Publication.objects.filter(authors__in=[author])
    return render(
        request,
        "people_info.html",
        {
            "author": author,
            "tags": author.tag_set.all(),
            "aliases": author.authoralias_set.all(),
            "publications": publications,
            "user": request.user,
            "departments": Department.objects.all(),
        },
    )


def update_view(request):
    department_id = request.GET.get("department_id")
    datefrom = request.GET.get(
        "datefrom",
        now_datetime() - timedelta(days=60),
    )
    dateto = request.GET.get(
        "dateto", now_datetime()
    )
    if isinstance(datefrom, str):
        datefrom = datetime.fromtimestamp(int(datefrom))
    if isinstance(dateto, str):
        dateto = datetime.fromtimestamp(int(dateto))
    assigned_to_dep = request.GET.get("assigned_to_department", False)
    if assigned_to_dep == "false":
        assigned_to_dep = False
    elif assigned_to_dep == "true":
        assigned_to_dep = True
    tags = request.GET.get("tags", "").split(",")
    if "" in tags:
        tags.remove("")
    query = Q(added_date__gte=datefrom, added_date__lte=dateto)
    if assigned_to_dep and department_id:
        query &= Q(department__id=department_id)
    publications = Publication.objects.filter(query)

    def tag_filter(pub):
        any_of_authors_has_tag = False
        for author in pub.authors.all():
            author_tags = list(map(lambda x: x.name, author.tag_set.all()))
            if set(tags).intersection(set(author_tags)) == set(tags):
                any_of_authors_has_tag = True
        return any_of_authors_has_tag

    publications = list(filter(tag_filter, publications))
    groups = {}
    for pub in publications:
        month_tag = f"{pub.added_date.month}.{pub.added_date.year}"
        groups.setdefault(
            month_tag,
            {
                "localized_name": dateformat.format(pub.added_date, "F Y"),
                "publications": [],
            },
        )
        groups[month_tag]["publications"].append(pub)
    return render(request, "updates_view.html", {"groups": groups.values()})


def account_profile(request):
    return redirect("/", permanent=True)
