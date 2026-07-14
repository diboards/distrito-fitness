"""
WSGI config for distrito_fitness project.
"""

import os
from django.core.wsgi import get_wsgi_application
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'distrito_fitness.settings')

# 🔥 FORÇAR MIGRAÇÕES NA INICIALIZAÇÃO DO SERVIDOR
try:
    print("🔄 Executando migrações...")
    call_command('makemigrations', 'vendas', interactive=False)
    call_command('migrate', interactive=False)
    print("✅ Migrações aplicadas com sucesso!")
except Exception as e:
    print(f"⚠️ Erro nas migrações: {e}")

application = get_wsgi_application()
