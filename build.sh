#!/bin/bash

echo "========================================="
echo "🚀 BUILD.SH EXECUTANDO"
echo "========================================="

pip install -r requirements.txt

# Adicionar a coluna imagem via SQL direto
python manage.py dbshell << 'EOF'
ALTER TABLE vendas_produto ADD COLUMN IF NOT EXISTS imagem varchar(200);
EOF

# Criar e aplicar migrações
python manage.py makemigrations vendas --noinput
python manage.py migrate vendas --noinput

# Coletar estáticos
python manage.py collectstatic --noinput

echo "✅ Build concluído!"
