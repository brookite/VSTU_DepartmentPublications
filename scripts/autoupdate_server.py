from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from autoupdate.strategy import *

scheduler = BlockingScheduler()
scheduler.add_job(global_autoupdate, CronTrigger.from_crontab(SETTINGS.cron_schedule))
scheduler.add_job(
    short_task_batch, IntervalTrigger(seconds=SETTINGS.short_tasks_check_interval)
)
scheduler.start()
