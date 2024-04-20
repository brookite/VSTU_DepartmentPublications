import schedule
from autoupdate.strategy import *

schedule.every(SETTINGS.short_tasks_wait_interval_seconds).seconds.do(short_task_batch)
schedule.every(15).minutes.do(global_autoupdate)

if __name__ == "__main__":
    print("Autoupdate server starting...")
    while True:
        schedule.run_pending()
        time.sleep(1)
