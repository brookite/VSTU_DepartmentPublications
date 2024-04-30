#!/bin/bash

set -e

exec python3.12 manage.py collectstatic --no-input
exec python3.12 manage.py makemigrations
exec python3.12 manage.py migrate
exec python3.12 manage.py runscript autoupdate_server &
exec python3.12 manage.py runserver 0.0.0.0:8000