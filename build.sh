#!/bin/bash

echo "========================================="
echo "🚀 BUILD.SH EXECUTANDO"
echo "========================================="

pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput

echo "✅ Build concluído!"
