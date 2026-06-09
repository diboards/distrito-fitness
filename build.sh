#!/bin/bash

echo "========================================="
echo "🚀 BUILD.SH EXECUTANDO"
echo "========================================="

pip install -r requirements.txt

# Criar migrações
python manage.py makemigrations vendas --noinput

# Aplicar migrações
python manage.py migrate vendas --noinput

# Coletar estáticos
python manage.py collectstatic --noinput

echo "✅ Build concluído!"
