#!/bin/bash

echo "========================================="
echo "🚀 BUILD.SH EXECUTANDO"
echo "========================================="

# Instalar dependências
pip install -r requirements.txt

# Remover migrações antigas
rm -f vendas/migrations/00*.py

# Criar migrações
python manage.py makemigrations vendas --noinput

# Forçar migração falsa para as tabelas existentes
python manage.py migrate vendas --fake --noinput

# Criar apenas a tabela ProdutoVariacao
python manage.py migrate vendas --fake-initial --noinput

# Tentar criar apenas a tabela que falta
python manage.py migrate vendas 0001_initial --noinput

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

echo "✅ Build concluído!"
