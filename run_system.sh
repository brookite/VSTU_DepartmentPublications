#!/bin/bash

python3.12 manage.py makemigrations
python3.12 manage.py migrate
python3.12 manage.py collectstatic --noinput
exec python3.12 manage.py runscript autoupdate_server &
exec python3.12 manage.py runserver 0.0.0.0:8000
