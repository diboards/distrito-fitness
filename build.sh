#!/bin/bash

echo "========================================="
echo "🚀 BUILD.SH EXECUTANDO"
echo "========================================="

# Instalar dependências
pip install -r requirements.txt

# Criar migrações
python manage.py makemigrations vendas --noinput

# Aplicar todas as migrações pendentes
python manage.py migrate vendas --noinput

# Se ainda tiver erro, renomear a coluna manualmente via SQL
python manage.py dbshell << EOF
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='vendas_produto' AND column_name='imagem_principal') THEN
        ALTER TABLE vendas_produto RENAME COLUMN imagem_principal TO imagem;
        RAISE NOTICE 'Coluna renomeada com sucesso';
    ELSE
        RAISE NOTICE 'Coluna imagem_principal não existe';
    END IF;
END $$;
EOF

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

echo "✅ Build concluído!"
