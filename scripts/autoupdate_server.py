from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from autoupdate.strategy import *

global_autoupdate_job = None
schedule = get_settings().cron_schedule
last_global_update_request = get_timestamps().last_global_update_request

LOCK_UPDATE = False


def schedule_observer(job):
    logger.debug("Проверка изменения расписания")
    global global_autoupdate_job
    global schedule
    global last_global_update_request

    if global_autoupdate_job and schedule != get_settings().cron_schedule:
        schedule = get_settings().cron_schedule
        global_autoupdate_job = global_autoupdate_job.reschedule(trigger=CronTrigger.from_crontab(schedule))
        logger.debug(f"Расписание было изменено на {calculate_next_global_update()}")

    if last_global_update_request != get_timestamps().last_global_update_request:
        last_global_update_request = get_timestamps().last_global_update_request
        logger.info("Начинаю внеплановое глобальное обновление по запросу")
        global_autoupdate_task(True)


def global_autoupdate_task(skip_update_university=False):
    global LOCK_UPDATE
    LOCK_UPDATE = True
    global_autoupdate(skip_update_university)
    LOCK_UPDATE = False


def short_autoupdate_task():
    if LOCK_UPDATE:
        return
    short_task_batch()


def run():
    logger.info("Запускаю планировщик задач автообновления...")
    scheduler = BlockingScheduler()
    try:
        global global_autoupdate_job
        global_autoupdate_job = scheduler.add_job(
            global_autoupdate_task, CronTrigger.from_crontab(schedule)
        )
        scheduler.add_job(
            short_autoupdate_task, IntervalTrigger(seconds=get_settings().short_tasks_check_interval)
        )
        scheduler.add_job(
            schedule_observer, IntervalTrigger(minutes=get_settings().reschedule_minutes), args=[global_autoupdate_job]
        )
        logger.info("Задачи автообновления добавлены. Начинаю планирование...")
        scheduler.start()
    except KeyboardInterrupt:
        scheduler.shutdown(wait=False)
