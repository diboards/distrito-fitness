#!/bin/bash

echo "========================================="
echo "🚀 BUILD.SH EXECUTANDO"
echo "========================================="

# Instalar dependências
pip install -r requirements.txt

# Criar e aplicar migrações
python manage.py makemigrations vendas --noinput
python manage.py migrate --noinput

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

echo "✅ Build concluído!"
