# vendas/migrations/0005_add_imagem_column.py
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('vendas', '0004_rename_imagem_selecionada_carrinhoitem_imagem'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE vendas_produto ADD COLUMN IF NOT EXISTS imagem varchar(200);",
            reverse_sql="ALTER TABLE vendas_produto DROP COLUMN IF EXISTS imagem;"
        ),
    ]
