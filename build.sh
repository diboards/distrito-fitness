#!/bin/bash

echo "========================================="
echo "🚀 BUILD.SH EXECUTANDO"
echo "========================================="

pip install -r requirements.txt

# 🔥 MIGRAÇÕES FORÇADAS
echo "📝 Criando migrações..."
python manage.py makemigrations vendas --noinput
python manage.py makemigrations --noinput

echo "⚡ Aplicando migrações..."
python manage.py migrate vendas --noinput
python manage.py migrate --noinput

echo "📁 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

echo "✅ Build concluído!"
