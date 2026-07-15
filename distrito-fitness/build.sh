#!/bin/bash
pip install -r requirements.txt
python migrate.py
python manage.py collectstatic --noinput