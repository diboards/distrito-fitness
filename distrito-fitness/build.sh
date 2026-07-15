#!/bin/bash

echo "========================================="
echo "🚀 BUILD.SH EXECUTANDO"
echo "========================================="

pip install -r requirements.txt

# 🔥 EXECUTAR MIGRAÇÕES
echo "📝 Executando migrações..."
python distrito_fitness/migrate.py

python manage.py collectstatic --noinput

echo "✅ Build concluído!"