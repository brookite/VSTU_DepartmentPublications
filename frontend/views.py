from django.db.models import Q
from django.shortcuts import render, redirect

from api.models import Author, Publication


def index(request):
    return render(request, "index.html", {"user": request.user})


def updates(request):
    return render(request, "updates.html", {"user": request.user})


def author_list(request):
    q = request.GET.get("q", "")
    dep_id = request.GET.get("department")
    query = Q(full_name__icontains=q) | Q(library_primary_name__icontains=q)
    if dep_id:
        query &= Q(department_id=dep_id)
    authors = Author.objects.filter(query)
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
        },
    )


def account_profile(request):
    return redirect("/", permanent=True)
