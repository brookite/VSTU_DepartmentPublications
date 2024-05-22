from django.urls import path

from frontend.views import *

urlpatterns = [
    path("", index),
    path("updates", updates),
    path("views/author_list", author_list),
    path("dumpLogs", dump_logs),
    path("views/author_info", author_details),
    path("views/updates_view", update_view),
    path("accounts/profile/", account_profile),
]
