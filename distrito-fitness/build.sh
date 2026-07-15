#!/bin/bash

echo "========================================="
echo "🚀 BUILD.SH EXECUTANDO"
echo "========================================="

pip install -r requirements.txt

# 🔥 EXECUTAR MIGRAÇÕES COM ARQUIVO SEPARADO
echo "📝 Executando migrações..."
python migrate.py

python manage.py collectstatic --noinput

echo "✅ Build concluído!"