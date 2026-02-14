from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (
    AuthorSuggestions,
    AuthorViewSet,
    FacultyDepartmentView,
    PlanViewSet,
    PublicationListView,
    SettingsViewSet,
    TagListView,
    stats,
    subscribe_email_toggle,
)

author_router = DefaultRouter()
author_router.register(r"authors", AuthorViewSet, basename="author")
settings_router = DefaultRouter()
settings_router.register(r"settings", SettingsViewSet, basename="settings")
plan_router = DefaultRouter()
plan_router.register(r"plan", PlanViewSet, basename="plan")

urlpatterns = [
    path("auth/", include("rest_framework.urls")),
    path("authorSuggestions/", AuthorSuggestions.as_view()),
    path("publications/", PublicationListView.as_view()),
    path("departments/", FacultyDepartmentView.as_view()),
    path("tags/", TagListView.as_view()),
    path("stats/", stats),
    path("subscribeEmail", subscribe_email_toggle),
]
urlpatterns += author_router.urls
urlpatterns += settings_router.urls
urlpatterns += plan_router.urls
