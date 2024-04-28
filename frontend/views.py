from django.shortcuts import render


def index(request):
    return render(request, "index.html")


def updates(request):
    return render(request, "updates.html")
