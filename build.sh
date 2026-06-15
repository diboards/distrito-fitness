python manage.py shell << 'EOF'
from vendas.models import Produto

print("=== CATEGORIAS DOS PRODUTOS ===")
for p in Produto.objects.all():
    print(f"Produto: {p.nome} - Categoria: '{p.categoria}' - Ativo: {p.ativo}")
EOF
