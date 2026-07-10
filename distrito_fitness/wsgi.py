#!/bin/bash

echo "========================================="
echo "🚀 BUILD.SH EXECUTANDO"
echo "========================================="

pip install -r requirements.txt

# 🔥 REMOVER MIGRAÇÕES ANTIGAS E RECRIAR
echo "📝 Recriando migrações..."
rm -f vendas/migrations/00*.py
python manage.py makemigrations vendas --noinput

echo "⚡ Aplicando migrações FORÇADAMENTE..."
python manage.py migrate vendas --noinput
python manage.py migrate --noinput

echo "📁 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

echo "✅ Build concluído!"
