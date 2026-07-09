#!/bin/bash

echo "========================================="
echo "🚀 BUILD.SH EXECUTANDO"
echo "========================================="

pip install -r requirements.txt

# Forçar criação e aplicação de migrações
python manage.py makemigrations vendas --noinput
python manage.py migrate vendas --noinput

python manage.py collectstatic --noinput

echo "✅ Build concluído!"
