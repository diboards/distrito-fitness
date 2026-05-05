# vendas/urls.py
from django.urls import path
from .import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from vendas.views import (  # Agora importa da pasta
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


urlpatterns = [
    path('', views.pagina_inicial, name='pagina_inicial'),
    path('index/', views.pagina_inicial, name='index'),
    path('lista_vendas/', views.lista_vendas, name='lista_vendas'),
    path('cadastrar_produto/', views.cadastrar_produto, name='cadastrar_produto'),
    path('vendas/nova/', views.nova_venda, name='nova_venda'),
    path('relatorios/', views.relatorios, name='relatorios'),
    path('editar/<int:venda_id>/', views.editar_venda, name='editar_venda'),
    path('venda/atualizar/<int:venda_id>/', views.atualizar_venda, name='atualizar_venda'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='pagina_inicial'), name='logout'),
    path('registrar-com-endereco/', views.registrar_com_endereco, name='registrar_com_endereco'),
    path('registrar/', views.registrar_usuario, name='registrar'),
    path('orcamento/', views.solicitar_orcamento, name='orcamento'),

    # Perfil do usuário
    path('meu-perfil/', views.meu_perfil, name='meu_perfil'),
    path('meus-enderecos/', views.meus_enderecos, name='meus_enderecos'),
    path('endereco/editar/<int:endereco_id>/', views.editar_endereco, name='editar_endereco'),
    path('endereco/deletar/<int:endereco_id>/', views.deletar_endereco, name='deletar_endereco'),
    path('endereco/principal/<int:endereco_id>/', views.definir_endereco_principal, name='definir_endereco_principal'),

    
    # RESET DE SENHA
    path('password_reset/', auth_views.PasswordResetView.as_view(
    template_name='vendas/auth/password_reset.html',
    email_template_name='vendas/auth/password_reset_email.txt',  # versão texto
    html_email_template_name='vendas/auth/password_reset_email.html',  # HTML real
    subject_template_name='vendas/auth/password_reset_subject.txt'
    ), name='password_reset'),

    path('password_reset_done/',
     auth_views.PasswordResetDoneView.as_view(
         template_name='vendas/auth/password_reset_done.html'
     ),
     name='password_reset_done'),

    path('reset/<uidb64>/<token>/',
     auth_views.PasswordResetConfirmView.as_view(
         template_name='vendas/auth/password_reset_confirm.html'
     ),
     name='password_reset_confirm'),

    path('reset_done/',
     auth_views.PasswordResetCompleteView.as_view(
         template_name='vendas/auth/password_reset_complete.html'
     ),
     name='password_reset_complete'),
    
    path('estoque/', views.estoque, name='estoque'),
    path('estoque/editar/<int:produto_id>/', views.editar_produto, name='editar_produto'),
    path('estoque/cadastrar/', views.cadastrar_produto, name='cadastrar_produto'),

    # URLs do seu sistema (fora do admin padrão)
    path('painel/pedidos/', views.gerenciar_pedidos, name='gerenciar_pedidos'),
    path('painel/pedido/<int:pedido_id>/status/', views.atualizar_status_entrega, name='atualizar_status_entrega'),
    
    # URLs do carrinho e produtos
    path('produto/<int:produto_id>/', views.detalhes_produto, name='detalhes_produto'),
    path('carrinho/adicionar/<int:produto_id>/', views.adicionar_carrinho, name='adicionar_carrinho'),
    path('carrinho/', views.visualizar_carrinho, name='visualizar_carrinho'),
    path('carrinho/remover/<int:item_id>/', views.remover_carrinho, name='remover_carrinho'),
    path('carrinho/atualizar/<int:item_id>/', views.atualizar_carrinho, name='atualizar_carrinho'),
    path('carrinho/count/', views.carrinho_count_api, name='carrinho_count_api'),
    
    # NOVAS URLs - Adicione estas
    path('calcular-frete-ajax/', views.calcular_frete_ajax, name='calcular_frete_ajax'),
    path('comprar-agora/<int:produto_id>/', views.comprar_agora, name='comprar_agora'),
    path('checkout/', views.checkout, name='checkout'),
    path('adicionar-endereco-checkout/', views.adicionar_endereco_checkout, name='adicionar_endereco_checkout'),
    path('excluir-endereco/<int:endereco_id>/', views.excluir_endereco, name='excluir_endereco'),
    path('finalizar-pedido/', views.finalizar_pedido, name='finalizar_pedido'),
    path('pagamento/', views.pagamento, name='pagamento'),

    path('processar-pagamento-cartao/<int:pedido_id>/', views.processar_pagamento_cartao, name='processar_pagamento_cartao'),
    
    path('processar-pagamento-pix/<int:pedido_id>/', views.processar_pagamento_pix, name='processar_pagamento_pix'),
    
    path('teste-conexao/', views.testar_conexao_mp, name='teste_conexao'),
    
    path('criar-pagamento/', views.criar_pagamento, name='criar_pagamento'), #novo

    path('pagamento/sucesso/<int:pedido_id>/', views.pagamento_sucesso, name='pagamento_sucesso'),
    path('pagamento/falha/<int:pedido_id>/', views.pagamento_falha, name='pagamento_falha'),
    path('pagamento/pendente/<int:pedido_id>/', views.pagamento_pendente, name='pagamento_pendente'),

    path('meus-pedidos/', views.meus_pedidos, name='meus_pedidos'), 
    path('pedido/<int:pedido_id>/', views.detalhes_pedido, name='detalhes_pedido'),
  
    # webhooks para receber confirmações de pagamento:
    path('webhook/mercadopago/', views.webhook_mercadopago, name='webhook_mercadopago'),
    path('api/verificar-pagamento/<int:pedido_id>/', views.verificar_status_pagamento, name='api_verificar_pagamento'),
    path('pedido/<int:pedido_id>/verificar-status/', views.verificar_status_pagamento, name='verificar_status_pagamento'),
    path('pedido/<int:pedido_id>/diagnostico/', views.diagnostico_pagamento, name='diagnostico_pagamento'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
