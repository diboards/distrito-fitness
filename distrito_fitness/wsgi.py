"""
WSGI config for distrito_fitness project.
"""

import os
from django.core.wsgi import get_wsgi_application
from django.core.management import call_command
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'distrito_fitness.settings')

# 🔥 EXECUTAR MIGRAÇÕES NA INICIALIZAÇÃO
print("🔄 Executando migrações...")
try:
    call_command('makemigrations', 'vendas', interactive=False)
    call_command('migrate', interactive=False)
    print("✅ Migrações aplicadas com sucesso!")
except Exception as e:
    print(f"⚠️ Erro nas migrações: {e}")

# 🔥 CRIAR SUPERUSUÁRIO
try:
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@admin.com',
            password='admin123'
        )
        print("✅ Superusuário criado: admin / admin123")
except Exception as e:
    print(f"⚠️ Erro ao criar superusuário: {e}")

application = get_wsgi_application()
