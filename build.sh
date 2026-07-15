#!/bin/bash

echo "========================================="
echo "🚀 BUILD.SH EXECUTANDO"
echo "========================================="

# Instalar dependências
pip install -r requirements.txt

# 🔥 FORÇAR MIGRAÇÕES
echo "📝 Criando migrações..."
python manage.py makemigrations vendas --noinput
python manage.py makemigrations --noinput

echo "⚡ Aplicando migrações..."
python manage.py migrate vendas --noinput
python manage.py migrate --noinput

# Criar superusuário automaticamente
echo "👤 Criando superusuário..."
python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@admin.com', 'admin123')
    print("✅ Superusuário criado: admin / admin123")
EOF

echo "📁 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

echo "✅ Build concluído!"
