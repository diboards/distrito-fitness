# vendas/migrations/0005_add_imagem_field.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('vendas', '0004_rename_imagem_selecionada_carrinhoitem_imagem'),
    ]

    operations = [
        migrations.AddField(
            model_name='produto',
            name='imagem',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
