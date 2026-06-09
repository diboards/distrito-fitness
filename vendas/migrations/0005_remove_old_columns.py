# vendas/migrations/0005_remove_old_columns.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('vendas', '0004_rename_imagem_selecionada_carrinhoitem_imagem'),
    ]

    operations = [
        # Remover campos antigos do modelo Produto
        migrations.RemoveField(
            model_name='produto',
            name='preco',
        ),
        migrations.RemoveField(
            model_name='produto',
            name='quantidade_estoque',
        ),
        migrations.RemoveField(
            model_name='produto',
            name='cor',
        ),
        migrations.RemoveField(
            model_name='produto',
            name='tamanho',
        ),
        migrations.RemoveField(
            model_name='produto',
            name='imagem',
        ),
    ]
