"""
WSGI config for distrito_fitness project.
"""

import os
from django.core.wsgi import get_wsgi_application
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'distrito_fitness.settings')

# 🔥 APLICAR MIGRAÇÕES NA INICIALIZAÇÃO
def run_migrations():
    try:
        print("🔄 Executando migrações...")
        call_command('makemigrations', 'vendas', interactive=False)
        call_command('migrate', interactive=False)
        print("✅ Migrações aplicadas com sucesso!")
    except Exception as e:
        print(f"⚠️ Erro nas migrações: {e}")

# Criar superusuário
def create_superuser():
    try:
        from django.contrib.auth import get_user_model
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

# Só executa depois que o Django estiver pronto
application = get_wsgi_application()

# Executa as funções após a aplicação estar pronta
try:
    run_migrations()
    create_superuser()
except Exception as e:
    print(f"⚠️ Erro na inicialização: {e}")