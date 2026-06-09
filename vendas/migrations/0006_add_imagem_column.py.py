# vendas/migrations/0006_add_imagem_column.py
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('vendas', '0005_clean_migration'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE vendas_produto ADD COLUMN IF NOT EXISTS imagem varchar(200);",
            reverse_sql="ALTER TABLE vendas_produto DROP COLUMN IF EXISTS imagem;"
        ),
    ]
