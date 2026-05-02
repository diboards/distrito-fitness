#!/usr/bin/env bash

pip install -r requirements.txt

python manage.py migrate

# criar usuario adm ativar se for o caso
#python manage.py createsuperuser --noinput || true