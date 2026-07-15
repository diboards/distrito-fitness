#!/bin/bash

echo "========================================="
echo "🚀 BUILD.SH EXECUTANDO"
echo "========================================="

pip install -r requirements.txt

# 🔥 Executar migrações via script
echo "📝 Executando migrações..."
python distrito_fitness/startup.py

python manage.py collectstatic --noinput

echo "✅ Build concluído!"