#!/bin/bash

echo "========================================="
echo "🚀 BUILD.SH EXECUTANDO"
echo "========================================="

pip install -r requirements.txt

# 🔥 EXECUTAR MIGRAÇÕES FORÇADAMENTE
echo "📝 Executando migrações..."
python -c "
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'distrito_fitness.settings')
django.setup()

from django.core.management import call_command
from django.contrib.auth import get_user_model

print('🔄 Executando migrações...')
call_command('makemigrations', 'vendas', interactive=False)
call_command('migrate', interactive=False)
print('✅ Migrações aplicadas!')

print('👤 Criando superusuário...')
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@admin.com', 'admin123')
    print('✅ Superusuário criado: admin / admin123')
"

python manage.py collectstatic --noinput

echo "✅ Build concluído!"