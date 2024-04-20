import datetime

from api.models import Settings as SettingsModel, Author
from api.models import Timestamps as TimestampsModel


class Settings:
    def __init__(self):
        # TODO: fix
        SettingsModel.objects.get_or_create(
            param_name="request_batch_size", param_value=3
        )
        SettingsModel.objects.get_or_create(
            param_name="short_task_batch_interval_seconds", param_value=5 * 3600
        )
        SettingsModel.objects.get_or_create(
            param_name="obsolescence_time_seconds", param_value=3
        )
        SettingsModel.objects.get_or_create(param_name="max_short_tasks", param_value=8)
        SettingsModel.objects.get_or_create(
            param_name="short_tasks_wait_interval_seconds", param_value=300
        )
        SettingsModel.objects.get_or_create(
            param_name="day_of_autoupdate", param_value="saturday"
        )
        SettingsModel.objects.get_or_create(
            param_name="time_autoupdate_seconds", param_value=3600 * 3
        )
        SettingsModel.objects.get_or_create(
            param_name="autoupdate_interval", param_value="week"
        )
        SettingsModel.objects.get_or_create(
            param_name="autoupdate_interval_length", param_value=1
        )

    @property
    def request_batch_size(self):
        return int(
            SettingsModel.objects.get(param_name="request_batch_size").param_value
        )

    @property
    def obsolescence_time_seconds(self):
        return int(
            SettingsModel.objects.get(
                param_name="obsolescence_time_seconds"
            ).param_value
        )

    @property
    def short_task_batch_interval_seconds(self):
        return int(
            SettingsModel.objects.get(
                param_name="short_task_batch_interval_seconds"
            ).param_value
        )

    @property
    def max_short_tasks(self):
        return int(SettingsModel.objects.get(param_name="max_short_tasks").param_value)

    @property
    def short_tasks_wait_interval_seconds(self):
        return int(
            SettingsModel.objects.get(
                param_name="short_tasks_wait_interval_seconds"
            ).param_value
        )

    @property
    def day_of_autoupdate(self):
        return str(
            SettingsModel.objects.get(param_name="day_of_autoupdate").param_value
        )

    @property
    def autoupdate_interval(self):
        return str(
            SettingsModel.objects.get(param_name="autoupdate_interval").param_value
        )

    @property
    def autoupdate_interval_length(self):
        return int(
            SettingsModel.objects.get(
                param_name="autoupdate_interval_length"
            ).param_value
        )

    def plan_autoupdate(self, interval: str, count: int, day_of_week: str = None):
        if interval not in ["day", "week", "month"]:
            raise ValueError("Invalid interval: " + interval)
        if day_of_week not in [
            None,
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]:
            raise ValueError("Invalid day of week: " + day_of_week)
        autoupdate_interval = SettingsModel.objects.get(
            param_name="autoupdate_interval"
        )
        autoupdate_interval.param_value = interval
        autoupdate_interval.save()

        interval_length = SettingsModel.objects.get(
            param_name="autoupdate_interval_length"
        )
        interval_length.param_value = count
        interval_length.save()

        day_of_autoupdate = SettingsModel.objects.get(param_name="day_of_autoupdate")
        day_of_autoupdate.param_value = day_of_week
        day_of_autoupdate.save()


class Timestamps:
    def __init__(self):
        TimestampsModel.objects.get_or_create(
            param_name="last_global_update", timestamp=datetime.datetime.now()
        )
        TimestampsModel.objects.get_or_create(
            param_name="last_short_tasks_batch", timestamp=0
        )

    @property
    def last_update(self):
        return Author.objects.order_by("-last_updated").first().last_updated

    @property
    def last_short_update(self):
        return TimestampsModel.objects.get(
            param_name="last_short_tasks_batch"
        ).timestamp

    @property
    def last_global_update(self):
        return TimestampsModel.objects.get(param_name="last_global_update").timestamp

    def register_global_update(self):
        update_field = TimestampsModel.objects.get("last_global_update")
        update_field.timestamp = datetime.datetime.now()
        update_field.save()

    def register_short_update(self):
        update_field = TimestampsModel.objects.get("last_short_tasks_batch")
        update_field.timestamp = datetime.datetime.now()
        update_field.save()
