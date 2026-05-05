
# vendas/views/__init__.py

# Importa do views.py principal
from .views import (
    pagina_inicial,
    estoque,
    lista_vendas,
    cadastrar_produto,
    nova_venda,
    relatorios,
    editar_venda,
    atualizar_venda,
    login_view,
    registrar_com_endereco,
    registrar_usuario,
    solicitar_orcamento,
)

# Importa dos outros módulos
from .meu_perfil import *
from .meus_enderecos import *
