#!/bin/bash

echo "========================================="
echo "🚀 BUILD.SH EXECUTANDO"
echo "========================================="

# Instalar dependências
pip install -r requirements.txt

# Aplicar migrações
python manage.py migrate vendas --noinput
python manage.py migrate --noinput

# 🔥 SCRIPT PARA CRIAR VARIAÇÕES E CORRIGIR PRODUTOS
python manage.py shell << 'EOF'
from vendas.models import Produto, ProdutoVariacao
from decimal import Decimal

print("=== VERIFICANDO PRODUTOS ===")

# 1. Mostrar produtos existentes
print("\n--- PRODUTOS CADASTRADOS ---")
for p in Produto.objects.all():
    print(f"ID: {p.id} - Nome: {p.nome} - Categoria: {p.categoria} - Ativo: {p.ativo}")
    print(f"   Variações: {p.variacoes.count()}")

# 2. Criar variações para produtos que não têm
print("\n--- CRIANDO VARIAÇÕES PARA PRODUTOS SEM VARIAÇÃO ---")
produtos_sem_variacao = Produto.objects.filter(variacoes__isnull=True)

if produtos_sem_variacao.exists():
    for p in produtos_sem_variacao:
        variacao = ProdutoVariacao.objects.create(
            produto=p,
            cor='Branco',
            tamanho='M',
            preco=Decimal('49.90'),
            quantidade_estoque=10
        )
        print(f"✅ Variação criada para: {p.nome} (ID: {variacao.id})")
else:
    print("Todos os produtos já têm variações.")

# 3. Verificar resultado final
print("\n--- RESULTADO FINAL ---")
for p in Produto.objects.all():
    print(f"{p.nome}: {p.variacoes.count()} variação(ões)")
    for v in p.variacoes.all():
        print(f"   - {v.cor}/{v.tamanho} - R${v.preco} - Estoque: {v.quantidade_estoque}")

print("\n=== SCRIPT CONCLUÍDO ===")
EOF

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

echo "✅ Build concluído!"
