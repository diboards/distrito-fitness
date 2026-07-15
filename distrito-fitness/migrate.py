# migrate.py
import os
import django
from django.core.management import call_command
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'distrito_fitness.settings')
django.setup()

print("🔄 Executando migrações...")
try:
    call_command('makemigrations', 'vendas', interactive=False)
    call_command('migrate', interactive=False)
    print("✅ Migrações aplicadas com sucesso!")
except Exception as e:
    print(f"⚠️ Erro nas migrações: {e}")

print("👤 Criando superusuário...")
try:
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@admin.com', 'admin123')
        print("✅ Superusuário criado: admin / admin123")
except Exception as e:
    print(f"⚠️ Erro ao criar superusuário: {e}")