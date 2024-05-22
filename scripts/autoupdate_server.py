from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from autoupdate.strategy import *

global_autoupdate_job = None

def schedule_observer(job):
    logger.debug("Проверка изменения расписания")
    global global_autoupdate_job
    if global_autoupdate_job:
        global_autoupdate_job = global_autoupdate_job.reschedule(CronTrigger.from_crontab(SETTINGS.cron_schedule))
        logger.debug("Расписание было изменено")


def run():
    logger.info("Запускаю планировщик задач автообновления...")
    scheduler = BlockingScheduler()
    global global_autoupdate_job
    global_autoupdate_job = scheduler.add_job(
        global_autoupdate, CronTrigger.from_crontab(SETTINGS.cron_schedule)
    )
    scheduler.add_job(
        short_task_batch, IntervalTrigger(seconds=SETTINGS.short_tasks_check_interval)
    )
    scheduler.add_job(
        schedule_observer, IntervalTrigger(minutes=SETTINGS.reschedule_minutes), args=[global_autoupdate_id]
    )
    logger.info("Задачи автообновления добавлены. Начинаю планирование...")
    scheduler.start()
