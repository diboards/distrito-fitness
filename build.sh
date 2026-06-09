#!/bin/bash

echo "========================================="
echo "🚀 BUILD.SH EXECUTANDO"
echo "========================================="

pip install -r requirements.txt

# Aplicar migrações
python manage.py migrate vendas --noinput
python manage.py collectstatic --noinput

echo "✅ Build concluído!"
