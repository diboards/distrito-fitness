#!/bin/bash

echo "========================================="
echo "🚀 BUILD.SH EXECUTANDO"
echo "========================================="

# Instalar dependências
pip install -r requirements.txt

# 🔥 FORÇAR MIGRAÇÕES COM SCRIPT SEPARADO
echo "📝 Executando migrações..."

# Cria um script Python temporário dentro do build
cat > /tmp/run_migrations.py << 'EOF'
import os
import sys
import django

# Configurar o Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'distrito_fitness.settings')
sys.path.append('/opt/render/project/src')

# Inicializar
django.setup()

from django.core.management import call_command
from django.contrib.auth import get_user_model

print("🔄 Executando migrações...")
call_command('makemigrations', 'vendas', interactive=False)
call_command('migrate', interactive=False)
print("✅ Migrações aplicadas com sucesso!")

print("👤 Criando superusuário...")
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@admin.com', 'admin123')
    print("✅ Superusuário criado: admin / admin123")
EOF

# Executa o script
python /tmp/run_migrations.py

# Coleta arquivos estáticos
python manage.py collectstatic --noinput

echo "✅ Build concluído!"