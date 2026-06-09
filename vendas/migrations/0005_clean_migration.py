# vendas/migrations/0005_clean_migration.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('vendas', '0004_rename_imagem_selecionada_carrinhoitem_imagem'),
    ]

    operations = [
        # Adicionar coluna imagem se não existir
        migrations.RunSQL(
            sql="ALTER TABLE vendas_produto ADD COLUMN IF NOT EXISTS imagem varchar(200);",
            reverse_sql="ALTER TABLE vendas_produto DROP COLUMN IF EXISTS imagem;"
        ),
        # Remover colunas antigas se existirem
        migrations.RunSQL(
            sql="ALTER TABLE vendas_produto DROP COLUMN IF EXISTS preco;",
            reverse_sql=""
        ),
        migrations.RunSQL(
            sql="ALTER TABLE vendas_produto DROP COLUMN IF EXISTS quantidade_estoque;",
            reverse_sql=""
        ),
        migrations.RunSQL(
            sql="ALTER TABLE vendas_produto DROP COLUMN IF EXISTS cor;",
            reverse_sql=""
        ),
        migrations.RunSQL(
            sql="ALTER TABLE vendas_produto DROP COLUMN IF EXISTS tamanho;",
            reverse_sql=""
        ),
    ]
