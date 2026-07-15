#!/bin/bash

echo "========================================="
echo "🚀 BUILD.SH EXECUTANDO"
echo "========================================="

pip install -r requirements.txt

# 🔥 EXECUTAR MIGRAÇÕES DIRETAMENTE
echo "📝 Executando migrações..."

# Usar python -c para executar o código inline
python -c "
import os
import sys

# Configurar o Django ANTES de qualquer import
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'distrito_fitness.settings')

# Adicionar o caminho do projeto
sys.path.append('/opt/render/project/src')

# Agora importar e configurar
import django
django.setup()

from django.core.management import call_command
from django.contrib.auth import get_user_model

print('🔄 Executando migrações...')
call_command('makemigrations', 'vendas', interactive=False)
call_command('migrate', interactive=False)
print('✅ Migrações aplicadas com sucesso!')

print('👤 Criando superusuário...')
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@admin.com', 'admin123')
    print('✅ Superusuário criado: admin / admin123')
"

python manage.py collectstatic --noinput

echo "✅ Build concluído!"