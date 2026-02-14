from django.urls import path

from frontend.views import (
    account_profile,
    author_details,
    author_list,
    dump_logs,
    index,
    reset_autoupdate_request,
    update_view,
    updates,
)

urlpatterns = [
    path("", index),
    path("updates", updates),
    path("views/author_list", author_list),
    path("dumpLogs", dump_logs),
    path("debugResetAutoupdateRequest", reset_autoupdate_request),
    path("views/author_info", author_details),
    path("views/updates_view", update_view),
    path("accounts/profile/", account_profile),
]
