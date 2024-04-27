import datetime

from api.models import Settings as SettingsModel, Author
from api.models import Timestamps as TimestampsModel


class Settings:
    def __init__(self):
        defaults = [
            {"param_name": "request_batch_size", "param_value": 3},
            {"param_name": "short_task_batch_update_delay", "param_value": 5 * 3600},
            {"param_name": "obsolescence_time_seconds", "param_value": 3},
            {"param_name": "max_short_tasks", "param_value": 8},
            {"param_name": "short_tasks_check_interval", "param_value": 300},
            {"param_name": "cron_schedule", "param_value": "2 0 * * 5"},
        ]

        for default in defaults:
            SettingsModel.objects.get_or_create(
                param_name=default["param_name"],
                defaults={"param_value": default["param_value"]},
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
    def short_task_batch_update_delay(self):
        return int(
            SettingsModel.objects.get(
                param_name="short_task_batch_update_delay"
            ).param_value
        )

    @property
    def max_short_tasks(self):
        return int(SettingsModel.objects.get(param_name="max_short_tasks").param_value)

    @property
    def cron_schedule(self):
        return SettingsModel.objects.get(param_name="cron_schedule").param_value

    @property
    def short_tasks_check_interval(self):
        return int(
            SettingsModel.objects.get(
                param_name="short_tasks_check_interval"
            ).param_value
        )

    def plan_autoupdate(
        self, interval: str, count: int, day_of_week: str = None, at_time: int = 0
    ):
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

        if day_of_week is not None:
            num_day_of_week = [
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
            ].index(day_of_week) + 1
        else:
            num_day_of_week = None
        every_day_month = None
        every_day_week = None
        every_month = None
        if interval == "day" and count > 7:
            every_day_month = count
        elif interval == "day" and count <= 7:
            every_day_week = count
        elif interval == "week":
            every_day_month = count
        elif interval == "month":
            every_day_month = count
        hour, minute = at_time // 3600, at_time % 3600
        if every_day_month:
            if num_day_of_week:
                cron = f"{hour} {minute} */{every_day_month} * {num_day_of_week}"
            else:
                cron = f"{hour} {minute} */{every_day_month} * *"
        elif every_day_week:
            cron = f"{hour} {minute} * * */{every_day_week}"
        elif every_month:
            if num_day_of_week:
                cron = f"{hour} {minute} * */{every_month} {num_day_of_week}"
            else:
                cron = f"{hour} {minute} * */{every_month} *"
        setting = SettingsModel.objects.get(param_name="cron_schedule")
        setting.param_value = cron
        setting.save()
        return cron


class Timestamps:
    def __init__(self):
        defaults = [
            {"param_name": "last_global_update", "timestamp": datetime.datetime.now()},
            {
                "param_name": "last_short_tasks_batch",
                "timestamp": datetime.datetime.fromtimestamp(0),
            },
        ]

        for default in defaults:
            TimestampsModel.objects.get_or_create(
                param_name=default["param_name"],
                defaults={"timestamp": default["timestamp"]},
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
