#!/bin/bash

echo "========================================="
echo "🚀 BUILD.SH EXECUTANDO"
echo "========================================="

pip install -r requirements.txt

# Executar migrações (redundante, mas seguro)
python manage.py makemigrations vendas --noinput
python manage.py migrate --noinput

python manage.py collectstatic --noinput

echo "✅ Build concluído!"
