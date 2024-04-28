from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from autoupdate.strategy import *


def schedule_observer(job):
    logger.debug("Проверка изменения расписания")
    job.reschedule(CronTrigger.from_crontab(SETTINGS.cron_schedule))


def run():
    # TODO: Autorefresh schedule
    logger.info("Запускаю планировщик задач автообновления...")
    scheduler = BlockingScheduler()
    global_autoupdate_id = scheduler.add_job(
        global_autoupdate, CronTrigger.from_crontab(SETTINGS.cron_schedule)
    )
    scheduler.add_job(
        short_task_batch, IntervalTrigger(seconds=SETTINGS.short_tasks_check_interval)
    )
    scheduler.add_job(
        schedule_observer, IntervalTrigger(minutes=5), args=[global_autoupdate_id]
    )
    logger.info("Задачи автообновления добавлены. Начинаю планирование...")
    scheduler.start()
