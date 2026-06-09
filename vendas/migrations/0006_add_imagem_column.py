# vendas/migrations/0006_add_imagem_column.py
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('vendas', '0005_clean_migration'),  # Ajuste para o nome da última migração
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                   WHERE table_name='vendas_produto' AND column_name='imagem') THEN
                        ALTER TABLE vendas_produto ADD COLUMN imagem varchar(200);
                        RAISE NOTICE 'Coluna imagem adicionada';
                    ELSE
                        RAISE NOTICE 'Coluna imagem já existe';
                    END IF;
                END $$;
            """,
            reverse_sql="ALTER TABLE vendas_produto DROP COLUMN IF EXISTS imagem;"
        ),
    ]
