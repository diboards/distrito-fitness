#!/bin/bash

echo "========================================="
echo "🚀 BUILD.SH EXECUTANDO"
echo "========================================="

# Instalar dependências
pip install -r requirements.txt

# Criar migrações
python manage.py makemigrations vendas --noinput

# Aplicar migrações (incluindo a nova)
python manage.py migrate vendas --noinput

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

echo "✅ Build concluído!"
