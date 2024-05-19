#!/bin/bash

python3.12 manage.py makemigrations
python3.12 manage.py migrate
python3.12 manage.py collectstatic --noinput
python3.12 manage.py createsuperuser --noinput --username admin --email poasvstu@yandex.ru
exec python3.12 manage.py runscript autoupdate_server &
exec python3.12 manage.py runserver 0.0.0.0:8000
