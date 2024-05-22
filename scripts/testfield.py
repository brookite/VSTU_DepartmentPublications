"""
Скрипт предназначен для выполнения администратором произвольного необходимого ему кода
в рамках контекста Django. Например, можно выполнить работу с ORM, непосредственно с помощью
кода.

Этот файл предназначен для тестирования, не рекомендуется отправлять его в production
"""

from autoupdate.strategy import *


def run():
    print(CronTrigger.from_crontab("0 14 * * 0").get_next_fire_time(None, now_datetime()))
