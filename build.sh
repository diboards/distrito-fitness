#!/bin/bash

echo "========================================="
echo "🚀 BUILD.SH EXECUTANDO"
echo "========================================="

# Instalar dependências
pip install -r requirements.txt

# Remover migrações antigas que podem estar causando conflito
rm -f vendas/migrations/00*.py

# Criar novas migrações
python manage.py makemigrations vendas --noinput

# Forçar a migração (ignorando erros de coluna)
python manage.py migrate vendas --noinput --fake-initial

# Criar e aplicar migrações para o resto
python manage.py makemigrations --noinput
python manage.py migrate --noinput

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

echo "✅ Build concluído!"
