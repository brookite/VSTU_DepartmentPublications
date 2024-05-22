import json
import logging

from api.models import Settings as SettingsModel, Author
from api.models import Timestamps as TimestampsModel

from utils.datetimeutils import now_datetime, from_timestamp

logger = logging.getLogger("api")

class Settings:
    def __init__(self):
        defaults = [
            {"param_name": "request_batch_size", "param_value": 3},
            {"param_name": "short_task_batch_update_delay", "param_value": 5 * 3600},
            {"param_name": "obsolescence_time_seconds", "param_value": 24 * 3600},
            {"param_name": "max_short_tasks", "param_value": 15},
            {"param_name": "short_tasks_check_interval", "param_value": 300},
            {"param_name": "cron_schedule", "param_value": "0 2 * * 5"},
            {"param_name": "reschedule_minutes", "param_value": 5},
            {"param_name": "short_batch_reset_timeout", "param_value": 3600}
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
    def reschedule_minutes(self):
        return int(
            SettingsModel.objects.get(param_name="reschedule_minutes").param_value
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
    def short_batch_reset_timeout(self):
        return int(SettingsModel.objects.get(param_name="short_batch_reset_timeout").param_value)

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
                "sunday",
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday"
            ].index(day_of_week)
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
            every_month = count
        hour, minute = at_time // 3600, at_time % 3600 // 60

        trace = {
            "every_day_month": every_day_month,
            "every_month": every_month,
            "interval": interval,
            "every_day_week": every_day_week,
            "day_of_week": day_of_week,
            "hour": hour,
            "minute": minute
        }
        logger.debug("Планирование с параметрами: {}".format(json.dumps(trace)))

        if every_day_month:
            if num_day_of_week:
                if every_day_month == 1:
                    cron = f"{minute} {hour} * * {num_day_of_week}"
                else:
                    cron = f"{minute} {hour} */{every_day_month} * {num_day_of_week}"
            else:
                if every_day_month == 1:
                    cron = f"{minute} {hour} * * *"
                else:
                    cron = f"{minute} {hour} */{every_day_month} * *"
        elif every_day_week:
            cron = f"{minute} {hour} * * */{every_day_week}"
        elif every_month:
            if num_day_of_week:
                cron = f"{minute} {hour} * */{every_month} {num_day_of_week}"
            else:
                cron = f"{minute} {hour} * */{every_month} *"
        setting = SettingsModel.objects.get(param_name="cron_schedule")
        setting.param_value = cron
        setting.save()
        return cron


class Timestamps:
    _last_update_request = None

    def __init__(self):
        defaults = [
            {
                "param_name": "last_global_update",
                "timestamp": now_datetime(),
            },
            {
                "param_name": "last_short_tasks_batch",
                "timestamp": from_timestamp(0),
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
        update_field = TimestampsModel.objects.get(param_name="last_global_update")
        update_field.timestamp = now_datetime()
        update_field.save()

    def register_short_update(self):
        update_field = TimestampsModel.objects.get(param_name="last_short_tasks_batch")
        update_field.timestamp = now_datetime()
        update_field.save()

    def clear_short_updates(self):
        s = Settings()
        now = now_datetime()
        if (Timestamps._last_update_request and
                (now - Timestamps._last_update_request).total_seconds() <= s.short_batch_reset_timeout):
            logger.debug("В коротком обновлении отказано")
            return False
        logger.info("Запрошено короткое обновление")
        data = TimestampsModel.objects.get(param_name="last_short_tasks_batch")
        data.timestamp = from_timestamp(0)
        data.save()
        Timestamps._last_update_request = now
        return True

