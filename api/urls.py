from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import *

author_router = DefaultRouter()
author_router.register(r"authors", AuthorViewSet, basename="author")
settings_router = DefaultRouter()
settings_router.register(r"settings", SettingsViewSet, basename="settings")

urlpatterns = [
    path("auth/", include("rest_framework.urls")),
    path("authorSuggestions/", AuthorSuggestions.as_view()),
    path("publications/", PublicationListView.as_view()),
    path("departments/", FacultyDepartmentView.as_view()),
    path("stats/", stats),
]
urlpatterns += author_router.urls
urlpatterns += settings_router.urls
