#!/bin/bash

echo "========================================="
echo "🚀 BUILD.SH EXECUTANDO"
echo "========================================="

pip install -r requirements.txt

# Executar SQL diretamente no banco usando python
python << 'PYEOF'
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'distrito_fitness.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    # Verificar se a coluna existe
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.columns 
        WHERE table_name='vendas_produto' AND column_name='imagem'
    """)
    exists = cursor.fetchone()[0]
    
    if not exists:
        print("Adicionando coluna imagem...")
        cursor.execute("ALTER TABLE vendas_produto ADD COLUMN imagem varchar(200)")
        print("Coluna imagem adicionada com sucesso!")
    else:
        print("Coluna imagem já existe")
PYEOF

# Agora criar e aplicar migrações
python manage.py makemigrations vendas --noinput
python manage.py migrate vendas --noinput
python manage.py collectstatic --noinput

echo "✅ Build concluído!"
