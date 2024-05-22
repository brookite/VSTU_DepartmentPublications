from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from autoupdate.strategy import *

global_autoupdate_job = None
schedule = SETTINGS.cron_schedule


def schedule_observer(job):
    logger.debug("Проверка изменения расписания")
    global global_autoupdate_job
    global schedule
    if global_autoupdate_job and schedule != SETTINGS.cron_schedule:
        schedule = SETTINGS.cron_schedule
        global_autoupdate_job = global_autoupdate_job.reschedule(trigger=CronTrigger.from_crontab(schedule))
        logger.debug(f"Расписание было изменено на {calculate_next_global_update()}")


def run():
    logger.info("Запускаю планировщик задач автообновления...")
    scheduler = BlockingScheduler()
    try:
        global global_autoupdate_job
        global_autoupdate_job = scheduler.add_job(
            global_autoupdate, CronTrigger.from_crontab(schedule)
        )
        scheduler.add_job(
            short_task_batch, IntervalTrigger(seconds=SETTINGS.short_tasks_check_interval)
        )
        scheduler.add_job(
            schedule_observer, IntervalTrigger(minutes=SETTINGS.reschedule_minutes), args=[global_autoupdate_job]
        )
        logger.info("Задачи автообновления добавлены. Начинаю планирование...")
        scheduler.start()
    except KeyboardInterrupt:
        scheduler.shutdown(wait=False)
