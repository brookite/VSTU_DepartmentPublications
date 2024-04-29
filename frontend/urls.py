from django.urls import path

from frontend.views import *

urlpatterns = [
    path("", index),
    path("updates", updates),
    path("views/author_list", author_list),
    path("views/author_info", author_details),
    path("accounts/profile/", account_profile),
]