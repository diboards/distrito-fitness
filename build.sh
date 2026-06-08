#!/bin/bash

echo "🚀 Iniciando build..."

# Instalar dependências
echo "📦 Instalando dependências..."
pip install -r requirements.txt

# Criar migrações
echo "📝 Criando migrações..."
python manage.py makemigrations vendas
python manage.py makemigrations

# Aplicar migrações
echo "⚡ Aplicando migrações..."
python manage.py migrate

# Coletar arquivos estáticos
echo "📁 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

echo "✅ Build concluído com sucesso!"
