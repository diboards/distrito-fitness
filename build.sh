#!/bin/bash

echo "========================================="
echo "🚀 BUILD.SH EXECUTANDO"
echo "========================================="

# Instalar dependências primeiro
echo "📦 Instalando dependências do requirements.txt..."
pip install -r requirements.txt

# Verificar se Django foi instalado
echo "🔍 Verificando instalação do Django..."
python -c "import django; print(f'Django version: {django.get_version()}')"

# Aplicar migrações
echo "📝 Aplicando migrações..."
python manage.py migrate vendas --noinput
python manage.py migrate --noinput

# Criar variações para produtos
echo "🔄 Criando variações para produtos..."
python manage.py shell << 'EOF'
from vendas.models import Produto, ProdutoVariacao
from decimal import Decimal

print("=== VERIFICANDO PRODUTOS ===")
for p in Produto.objects.all():
    if p.variacoes.count() == 0:
        ProdutoVariacao.objects.create(
            produto=p,
            cor='Branco',
            tamanho='M',
            preco=Decimal('49.90'),
            quantidade_estoque=10
        )
        print(f"✅ Variação criada para: {p.nome}")
    else:
        print(f"⏭️ {p.nome} já tem variação")
EOF

# Coletar arquivos estáticos
echo "📁 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

echo "✅ Build concluído!"
