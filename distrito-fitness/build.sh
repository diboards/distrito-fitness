#!/bin/bash

echo "========================================="
echo "🚀 BUILD.SH EXECUTANDO"
echo "========================================="

pip install -r requirements.txt

# 🔥 EXECUTAR MIGRAÇÕES VIA SCRIPT
echo "📝 Executando migrações..."
python migrate.py

python manage.py collectstatic --noinput

echo "✅ Build concluído!"