#!/bin/bash

echo "========================================="
echo "🚀 BUILD.SH EXECUTANDO"
echo "========================================="

# Instalar dependências
pip install -r requirements.txt

# Remover migrações antigas
rm -f vendas/migrations/00*.py

# Criar novas migrações
python manage.py makemigrations vendas --noinput

# Criar a tabela manualmente via SQL
echo "Criando tabela vendas_produtovariacao manualmente..."

python manage.py shell << EOF
from django.db import connection
from django.contrib.auth.models import User

with connection.cursor() as cursor:
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vendas_produtovariacao (
                id SERIAL PRIMARY KEY,
                produto_id INTEGER NOT NULL,
                cor VARCHAR(20) NOT NULL,
                tamanho VARCHAR(10) NOT NULL,
                preco NUMERIC(10,2) NOT NULL,
                quantidade_estoque INTEGER NOT NULL DEFAULT 0,
                imagem VARCHAR(200)
            )
        """)
        print("Tabela vendas_produtovariacao criada com sucesso!")
    except Exception as e:
        print(f"Erro: {e}")
EOF

# Forçar migração
python manage.py migrate vendas --fake --noinput
# No shell do Render, execute:
python manage.py makemigrations vendas --empty --name remove_old_columns
# Coletar arquivos estáticos
python manage.py collectstatic --noinput

echo "✅ Build concluído!"
