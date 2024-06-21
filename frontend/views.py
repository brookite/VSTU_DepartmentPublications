import json
import os
import tempfile
import zipfile
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils import dateformat

from api import models
from api.models import Author, Publication, Department, Tag
from api.settings import Settings
from autoupdate.api import calculate_next_update, calculate_next_global_update
from departmentpublications import settings
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
    tags = request.GET.getlist("tags")
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
    tags = request.GET.getlist("tags")
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
                "month_firstday": datetime(pub.added_date.year, pub.added_date.month, 1),
                "localized_name": dateformat.format(pub.added_date, "F Y"),
                "publications": [],
            },
        )
        groups[month_tag]["publications"].append(pub)
    return render(request, "updates_view.html", {"groups": sorted(groups.values(), key=lambda x: x["month_firstday"], reverse=True)})


def account_profile(request):
    return redirect("/", permanent=True)


@login_required
def dump_logs(request):
    def datetime_converter(o):
        if isinstance(o, datetime):
            return o.isoformat()
        raise TypeError(f"Type {type(o)} not serializable")

    stats_data = {"settings": {}, "stats": {}}
    for param in models.Settings.objects.all():
        stats_data["settings"][param.param_name] = param.param_value
    for stat in models.Timestamps.objects.all():
        stats_data["stats"][stat.param_name] = stat.timestamp

    logs_dir = os.path.join(settings.BASE_DIR, 'logs')
    if not os.path.exists(logs_dir):
        return HttpResponse("Logs directory does not exist", status=404)

    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
        archive_path = tmp_file.name

    try:
        with zipfile.ZipFile(archive_path, 'w') as archive:
            for foldername, subfolders, filenames in os.walk(logs_dir):
                for filename in filenames:
                    file_path = os.path.join(foldername, filename)
                    archive.write(file_path, os.path.relpath(file_path, logs_dir))

            stats_json_path = os.path.join(tempfile.gettempdir(), 'stats.json')
            with open(stats_json_path, 'w') as stats_file:
                json.dump(stats_data, stats_file, default=datetime_converter, indent=4)

            archive.write(stats_json_path, 'stats.json')

        with open(archive_path, 'rb') as archive_file:
            response = HttpResponse(archive_file.read(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename=logs_archive.zip'
            return response

    finally:
        if os.path.exists(archive_path):
            os.remove(archive_path)
        if os.path.exists(stats_json_path):
            os.remove(stats_json_path)
