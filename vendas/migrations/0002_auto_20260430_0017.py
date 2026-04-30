from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('vendas', 'ULTIMA_MIGRATION_AQUI'),
    ]

    operations = [
        migrations.AddField(
            model_name='pedido',
            name='status_pagamento',
            field=models.CharField(max_length=20, default='pendente'),
        ),
        migrations.AddField(
            model_name='pedido',
            name='status_entrega',
            field=models.CharField(max_length=20, default='aguardando'),
        ),
    ]