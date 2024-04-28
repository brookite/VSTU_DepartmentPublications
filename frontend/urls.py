from django.urls import path

from frontend.views import *

urlpatterns = [path("", index), path("updates", updates)]
