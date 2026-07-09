#!/bin/bash

echo "========================================="
echo "🚀 BUILD.SH EXECUTANDO"
echo "========================================="

pip install -r requirements.txt

# 🔥 FORÇAR CRIAÇÃO E APLICAÇÃO DE MIGRAÇÕES
echo "📝 Criando migrações..."
python manage.py makemigrations vendas --noinput

echo "⚡ Aplicando migrações..."
python manage.py migrate vendas --noinput

echo "📁 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

echo "✅ Build concluído!"
