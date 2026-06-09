# vendas/migrations/0006_rename_imagem_column.py
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('vendas', '0005_remove_old_columns'),
    ]

    operations = [
        migrations.RenameField(
            model_name='produto',
            old_name='imagem_principal',
            new_name='imagem',
        ),
    ]
