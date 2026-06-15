#!/bin/bash

echo "========================================="
echo "🚀 BUILD.SH EXECUTANDO"
echo "========================================="

pip install -r requirements.txt

# Aplicar migrações
python manage.py migrate vendas --noinput
python manage.py migrate --noinput

# 🔥 SCRIPT PARA CRIAR VARIAÇÕES PARA PRODUTOS SEM VARIAÇÃO
python manage.py shell << 'EOF'
from vendas.models import Produto, ProdutoVariacao
from decimal import Decimal

print("=== VERIFICANDO PRODUTOS SEM VARIAÇÃO ===")
produtos_sem_variacao = Produto.objects.filter(variacoes__isnull=True)

if produtos_sem_variacao.exists():
    print(f"Encontrados {produtos_sem_variacao.count()} produtos sem variação.")
    for p in produtos_sem_variacao:
        # Criar uma variação padrão
        ProdutoVariacao.objects.create(
            produto=p,
            cor='Branco',
            tamanho='M',
            preco=Decimal('49.90'),
            quantidade_estoque=10
        )
        print(f"✓ Variação criada para: {p.nome}")
else:
    print("Todos os produtos já têm variações.")
EOF

python manage.py collectstatic --noinput

echo "✅ Build concluído!"
