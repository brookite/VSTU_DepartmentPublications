from django.apps import AppConfig
from autoupdate.api import initialize_settings


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"

    def ready(self):
        initialize_settings()
