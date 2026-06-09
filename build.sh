#!/bin/bash

echo "========================================="
echo "🚀 BUILD.SH EXECUTANDO"
echo "========================================="

pip install -r requirements.txt

# Limpar migrações problemáticas
rm -f vendas/migrations/0005_*.py
rm -f vendas/migrations/0006_*.py

# Criar nova migração
python manage.py makemigrations vendas --noinput

# Aplicar migrações
python manage.py migrate vendas --noinput

# Coletar estáticos
python manage.py collectstatic --noinput

echo "✅ Build concluído!"
