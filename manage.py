
# manage.py
#!/usr/bin/env python
import os
import sys
import subprocess

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'distrito_fitness.settings')
    
    # Executar migrações automaticamente se estiver no Render
    if os.environ.get('RENDER'):
        print("🔄 Executando migrações...")
        subprocess.run([sys.executable, "manage.py", "makemigrations", "vendas", "--noinput"])
        subprocess.run([sys.executable, "manage.py", "migrate", "--noinput"])
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
