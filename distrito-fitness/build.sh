#!/bin/bash

echo "========================================="
echo "🚀 BUILD.SH EXECUTANDO"
echo "========================================="

pip install -r requirements.txt

# 🔥 FORÇAR MIGRAÇÕES NO DEPLOY
python manage.py makemigrations vendas --noinput
python manage.py migrate vendas --noinput
python manage.py migrate --noinput

python manage.py collectstatic --noinput

echo "✅ Build concluído!"