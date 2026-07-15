#!/bin/bash

echo "========================================="
echo "🚀 BUILD.SH EXECUTANDO"
echo "========================================="

pip install -r requirements.txt

# Apenas coleta de estáticos (as migrações serão no wsgi.py)
python manage.py collectstatic --noinput

echo "✅ Build concluído!"