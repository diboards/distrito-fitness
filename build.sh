#!/bin/bash

echo "========================================="
echo "🚀 BUILD.SH EXECUTANDO"
echo "========================================="

pip install -r requirements.txt

echo "📝 Aplicando migrações..."
python manage.py migrate vendas --noinput
python manage.py migrate --noinput

echo "🔄 Criando variações para produtos..."
python manage.py shell << 'EOF'
from vendas.models import Produto, ProdutoVariacao
from decimal import Decimal

print("=== INICIANDO CRIAÇÃO DE VARIAÇÕES ===")

# Listar todos os produtos
produtos = Produto.objects.all()
print(f"Total de produtos encontrados: {produtos.count()}")

for p in produtos:
    variacoes_count = p.variacoes.count()
    print(f"Produto: {p.nome} - Variações atuais: {variacoes_count}")
    
    if variacoes_count == 0:
        # Criar variação padrão
        ProdutoVariacao.objects.create(
            produto=p,
            cor='Branco',
            tamanho='M',
            preco=Decimal('49.90'),
            quantidade_estoque=10
        )
        print(f"  ✅ Variação criada para: {p.nome}")
    else:
        print(f"  ⏭️ Produto já tem variação")

print("=== VERIFICAÇÃO FINAL ===")
for p in Produto.objects.all():
    print(f"{p.nome}: {p.variacoes.count()} variação(ões)")
EOF

python manage.py collectstatic --noinput
echo "✅ Build concluído!"
