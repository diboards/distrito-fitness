#!/bin/bash

echo "🚀 Iniciando build..."

# Instalar dependências
pip install -r requirements.txt

# Remover migrações antigas (se houver conflito)
rm -f vendas/migrations/00*.py

# Criar novas migrações
python manage.py makemigrations vendas --noinput
python manage.py makemigrations --noinput

# Aplicar migrações FORÇADAMENTE
python manage.py migrate vendas --noinput
python manage.py migrate --noinput

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

echo "✅ Build concluído!"
