"""
Скрипт предназначен для выполнения администратором произвольного необходимого ему кода
в рамках контекста Django. Например, можно выполнить работу с ORM, непосредственно с помощью
кода.

Этот файл предназначен для тестирования, не рекомендуется отправлять его в production
"""

from autoupdate.strategy import *


def run():
    try:
        global_autoupdate(skip_university_update=True)
    except:
        logger.error("Exception", exc_info=True)
