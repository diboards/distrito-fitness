# vendas/views.py
from decimal import Decimal
from django.db import IntegrityError
from datetime import datetime, timedelta
from urllib.parse import quote
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Sum, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.dateparse import parse_date
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required


from collections import OrderedDict
from django.http import HttpResponseBadRequest
from django.views.decorators.http import require_POST
from .models import Produto, Venda, CarrinhoItem, EnderecoEntrega, Pedido, ItemPedido
from .forms import VendaForm, ProdutoForm, OrcamentoForm, UsuarioComEnderecoForm

import json, os
import requests
import mercadopago
from django.conf import settings

from .utils import get_itens_carrinho

from django.contrib.auth.models import User

def criar_admin():
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@email.com',
            password='123456'
        )

@login_required
def testar_conexao_mp(request):
    from django.conf import settings
    import mercadopago
    import requests
    
    print("=== TESTANDO CREDENCIAIS ===")
    print(f"Access Token: {settings.MERCADOPAGO_ACCESS_TOKEN}")
    print(f"Sandbox: {settings.MERCADOPAGO_SANDBOX}")
    
    # Teste DIRETO com a API
    url = "https://api.mercadopago.com/v1/payment_methods"
    headers = {
        "Authorization": f"Bearer {settings.MERCADOPAGO_ACCESS_TOKEN}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Resposta: {response.text}")
        
        if response.status_code == 200:
            print("✅ Conexão bem-sucedida!")
            return render(request, 'vendas/teste_conexao.html', {
                'status': response.status_code,
                'message': 'Conexão bem-sucedida!',
                'credencial': settings.MERCADOPAGO_ACCESS_TOKEN
            })
        else:
            print("❌ Erro na conexão")
            return render(request, 'vendas/teste_conexao.html', {
                'status': response.status_code,
                'message': response.text,
                'credencial': settings.MERCADOPAGO_ACCESS_TOKEN
            })
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return render(request, 'vendas/teste_conexao.html', {
            'error': str(e),
            'credencial': settings.MERCADOPAGO_ACCESS_TOKEN
        })

#Sacola de compras

def detalhes_produto(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)

     # Calculando descontos e parcelamento
    preco_pix = (produto.preco * Decimal("0.90")).quantize(Decimal("0.01"))  # 10% OFF no pix
    preco_parcela = (produto.preco / Decimal("4")).quantize(Decimal("0.01")) # parcelado em 4x

    # traz todas as variações do mesmo modelo (mesmo nome)
    variacoes = Produto.objects.filter(nome=produto.nome, ativo=True).order_by('cor', 'tamanho')

    # organiza por cor: guarda primeira imagem encontrada e lista de tamanhos (valores)
    colors = OrderedDict()
    sizes_by_color = {}

    for var in variacoes:
        cor = var.cor  # valor armazenado no DB, ex: 'Vermelho', 'Azul', ...
        cor_display = var.get_cor_display()
        if cor not in colors:
            colors[cor] = {
                'cor': cor,
                'cor_display': cor_display,
                'imagem': var.imagem.url if var.imagem else ''
            }
            sizes_by_color[cor] = []
        # adiciona tamanho (valor armazenado, ex 'M', 'G')
        if var.tamanho not in sizes_by_color[cor]:
            sizes_by_color[cor].append(var.tamanho)

    # mapeamento para mostrar label do tamanho (value -> label)
    size_labels = {val: label for val, label in Produto.TAMANHO_CHOICES}

    context = {
        'produto': produto,
        "preco_pix": preco_pix,
        "preco_parcela": preco_parcela,
        'colors_list': list(colors.values()),
        'sizes_by_color': sizes_by_color,
        'size_labels': size_labels,
        # também passamos JSON já pronto para o JS sem precisar usar json_script
        'colors_json': json.dumps(list(colors.values())),
        'sizes_json': json.dumps(sizes_by_color),
        'size_labels_json': json.dumps(size_labels),
    }
    return render(request, 'vendas/detalhes_produto.html', context)

    
def adicionar_carrinho(request, produto_id):
    if request.method == 'POST':
        produto = get_object_or_404(Produto, id=produto_id)

        try:
            quantidade = int(request.POST.get('quantidade', 1))
        except:
            quantidade = 1

        cor = request.POST.get('cor', '')
        tamanho = request.POST.get('tamanho', '')
        action = request.POST.get('action', 'carrinho')

        if not request.user.is_authenticated and action == 'comprar':
            request.session['compra_rapida'] = {
                'produto_id': produto_id,
                'quantidade': quantidade,
                'cor': cor,
                'tamanho': tamanho,
                'action': action
            }
            return redirect('login')

        if request.user.is_authenticated:
            variacao = Produto.objects.filter(
                nome=produto.nome, cor=cor, tamanho=tamanho, ativo=True
            ).first()

            imagem = (
                variacao.imagem if variacao and variacao.imagem
                else produto.imagem
            )

            item, created = CarrinhoItem.objects.get_or_create(
                usuario=request.user,
                produto=produto,
                cor_selecionada=cor,
                tamanho_selecionado=tamanho,
                defaults={
                    'quantidade': quantidade,
                    'imagem_selecionada': imagem
                }
            )

            if not created:
                item.quantidade += quantidade
                item.imagem_selecionada = imagem
                item.save()

            messages.success(request, f'{produto.nome} adicionado ao carrinho!')

            if action == 'comprar':
                return redirect('visualizar_carrinho')
            return redirect('detalhes_produto', produto_id=produto_id)

    return redirect('pagina_inicial')

def carrinho_count_api(request):
    try:
        # usuário logado → usa banco
        if request.user.is_authenticated:
            count = CarrinhoItem.objects.filter(usuario=request.user).count()
            return JsonResponse({'count': count})

        # usuário NÃO logado → usa sessão
        carrinho = request.session.get('carrinho', {})

        if not isinstance(carrinho, dict):
            return JsonResponse({'count': 0})

        total = 0
        for item in carrinho.values():
            if isinstance(item, dict):
                total += int(item.get('quantidade', 0))

        return JsonResponse({'count': total})

    except Exception as e:
        print('ERRO carrinho_count_api:', str(e))
        return JsonResponse({'count': 0})

@login_required
def visualizar_carrinho(request):
    # busca todos os itens do carrinho do usuário logado
    itens_carrinho = CarrinhoItem.objects.filter(usuario=request.user)

    # soma dos subtotais
    total = sum(item.subtotal for item in itens_carrinho)

    # pega o endereço principal
    endereco_principal = None
    enderecos = request.user.enderecos.all()
    if enderecos.exists():
        endereco_principal = enderecos.filter(principal=True).first() or enderecos.first()

    return render(request, 'vendas/carrinho.html', {
        'itens_carrinho': itens_carrinho,
        'total': total,
        'endereco_principal': endereco_principal,
        'enderecos': enderecos,
    })

@login_required
def remover_carrinho(request, item_id):
    item = get_object_or_404(CarrinhoItem, id=item_id, usuario=request.user)
    item.delete()
    messages.success(request, 'Item removido do carrinho!')
    return redirect('visualizar_carrinho')

def atualizar_carrinho(request, item_id):
    item = get_object_or_404(CarrinhoItem, id=item_id, usuario=request.user)

    # corrige o typo: 'quantidade'
    try:
        quantidade = int(request.POST.get('quantidade', 1))
    except (ValueError, TypeError):
        quantidade = 1

    if quantidade > 0:
        item.quantidade = quantidade
        item.save()
        subtotal_item = float(item.subtotal)
    else:
        # remover item se quantidade <= 0
        item.delete()
        subtotal_item = 0.0

    # recalcula total e contador
    itens = CarrinhoItem.objects.filter(usuario=request.user)
    total = float(sum(i.subtotal for i in itens))
    count = itens.count()

    # se for requisição AJAX, retorna JSON (para atualizar frontend sem reload)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'item_id': int(item_id),
            'subtotal_item': subtotal_item,
            'total': total,
            'count': count
        })

    # fallback: redireciona normalmente (caso não seja AJAX)
    messages.success(request, 'Carrinho atualizado!')
    return redirect('visualizar_carrinho')

@csrf_exempt
def calcular_frete_ajax(request):
    if request.method == 'POST':
        cep = request.POST.get('cep')
        produto_id = request.POST.get('produto_id')
        quantidade = int(request.POST.get('quantidade', 1))
        
        try:
            produto = Produto.objects.get(id=produto_id)
            subtotal = produto.preco * quantidade
            
            # Simulação de cálculo de frete
            if subtotal > 100:
                frete = 0.00
            else:
                frete = 15.00
            
            total = subtotal + frete
            
            return JsonResponse({
                'success': True,
                'frete': f'R$ {frete:.2f}',
                'total': f'R$ {total:.2f}',
                'frete_gratis': frete == 0
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Requisição inválida'})

@login_required
def comprar_agora(request, produto_id):
    if request.method == 'POST':
        produto = get_object_or_404(Produto, id=produto_id)
        quantidade = int(request.POST.get('quantidade', 1))
        cor = request.POST.get('cor', '')
        tamanho = request.POST.get('tamanho', '')
        
        # Limpa o carrinho atual
        CarrinhoItem.objects.filter(usuario=request.user).delete()
        
        # Adiciona o produto ao carrinho
        CarrinhoItem.objects.create(
            usuario=request.user,
            produto=produto,
            quantidade=quantidade,
            cor_selecionada=cor,
            tamanho_selecionado=tamanho
        )
        
        messages.success(request, f'{produto.nome} adicionado ao carrinho!')
        return redirect('checkout')
    
    return redirect('detalhes_produto', produto_id=produto_id)

@login_required
def finalizar_pedido(request):
    if not request.user.is_authenticated:
        messages.warning(request, 'Faça login para finalizar o pedido')
        return redirect('login')
    
    itens_carrinho = CarrinhoItem.objects.filter(usuario=request.user)
    
    if not itens_carrinho.exists():
        messages.warning(request, 'Seu carrinho está vazio!')
        return redirect('pagina_inicial')
    
    # REDIRECIONE DIRETAMENTE PARA O CHECKOUT
    return redirect('checkout')


@login_required
def meus_pedidos(request):
    pedidos = Pedido.objects.filter(usuario=request.user).prefetch_related(
        'itens_pedido', 
        'itens_pedido__produto'
    )

    for pedido in pedidos:
        status = pedido.status

        pedido.is_pendente = status in ['pendente', 'aguardando_aprovacao']
        pedido.is_aprovado = status in ['aprovado']
        pedido.is_andamento = status in ['processando', 'enviado']
        pedido.is_enviado = status == 'enviado'
        pedido.is_entregue = status == 'entregue'
        pedido.is_cancelado = status == 'cancelado'

        if pedido.is_cancelado:
            pedido.progresso = 100
        elif pedido.is_entregue:
            pedido.progresso = 100
        elif status == 'enviado':
            pedido.progresso = 80
        elif status == 'processando':
            pedido.progresso = 60
        elif pedido.is_aprovado:
            pedido.progresso = 40
        elif pedido.is_pendente:
            pedido.progresso = 20
        else:
            pedido.progresso = 0

    return render(request, 'vendas/meus_pedidos.html', {
        'pedidos': pedidos
    })
# Views Checkout 

@login_required
def checkout(request):
    itens_carrinho = CarrinhoItem.objects.filter(usuario=request.user)
    
    if not itens_carrinho.exists():
        messages.warning(request, 'Seu carrinho está vazio!')
        return redirect('pagina_inicial')
    
    total = sum(item.subtotal for item in itens_carrinho)
    enderecos = EnderecoEntrega.objects.filter(usuario=request.user)
    
    # Verificar se é uma requisição AJAX (apenas uma vez, fora do POST)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if request.method == 'POST':
        print("=== DADOS RECEBIDOS NO POST ===")
        print("endereco_id:", request.POST.get('endereco_id'))
        print("metodo_pagamento:", request.POST.get('metodo_pagamento'))
        print("tipo_entrega:", request.POST.get('tipo_entrega'))
        print("is_ajax:", is_ajax)
        
        # VERIFICAR SE É UMA AÇÃO DE ADICIONAR ENDEREÇO
        if request.POST.get('action') == 'adicionar_endereco':
            return adicionar_endereco_checkout(request)
        
        endereco_id = request.POST.get('endereco_id')
        metodo_pagamento = request.POST.get('metodo_pagamento')
        tipo_entrega = request.POST.get('tipo_entrega')
        
        if not endereco_id or not metodo_pagamento:
            if is_ajax:
                return JsonResponse({'erro': 'Endereço e método de pagamento são obrigatórios'}, status=400)
            messages.error(request, 'Por favor, selecione um endereço e método de pagamento.')
            return redirect('checkout')
        
        try:
            endereco = get_object_or_404(EnderecoEntrega, id=endereco_id, usuario=request.user)
            
            # Calcular frete
            from decimal import Decimal
            frete = Decimal('15.00') if tipo_entrega == 'entrega' else Decimal('0.00')
            total_com_frete = total + frete
            
            # Aplicar desconto PIX
            if metodo_pagamento == 'pix':
                total_com_frete = total_com_frete * Decimal('0.90')  # 10% de desconto
            
            # Criar pedido
            pedido = Pedido.objects.create(
                usuario=request.user,
                total=total_com_frete,
                endereco_entrega=endereco,
                status='pendente',
                metodo_pagamento=metodo_pagamento,
                tipo_entrega=tipo_entrega,
                frete=frete
            )
            
            print(f"Pedido criado: #{pedido.id}")
            
            # Criar itens do pedido
            for item_carrinho in itens_carrinho:
                ItemPedido.objects.create(
                    pedido=pedido,
                    produto=item_carrinho.produto,
                    quantidade=item_carrinho.quantidade,
                    cor_selecionada=item_carrinho.cor_selecionada,
                    tamanho_selecionado=item_carrinho.tamanho_selecionado,
                    preco_unitario=item_carrinho.produto.preco
                )
                print(f"Item adicionado: {item_carrinho.produto.nome}")
            
            # Limpar carrinho
            itens_carrinho.delete()
            
            # Processar pagamento baseado no método escolhido
            if metodo_pagamento == 'pix':
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'pedido_id': pedido.id,
                        'metodo': 'pix',
                        'redirect_url': reverse('processar_pagamento_pix', args=[pedido.id])
                    })
                else:
                    print(f"DEBUG: Redirecionando para PIX do pedido {pedido.id}")
                    return redirect('processar_pagamento_pix', pedido_id=pedido.id)
                    
            elif metodo_pagamento == 'cartao':
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'pedido_id': pedido.id,
                        'metodo': 'cartao',
                        'total': float(pedido.total)
                    })
                else:
                    print(f"DEBUG: Redirecionando para página de pagamento com cartão do pedido {pedido.id}")
                    return redirect('processar_pagamento_cartao', pedido_id=pedido.id)
            
        except Exception as e:
            print(f"ERRO: {str(e)}")
            import traceback
            traceback.print_exc()
            
            if is_ajax:
                return JsonResponse({'erro': str(e)}, status=500)
            messages.error(request, f'Erro ao processar pedido: {str(e)}')
            return redirect('checkout')
    
    # SE FOR GET (mostrar o formulário)
    return render(request, 'vendas/checkout.html', {
        'itens_carrinho': itens_carrinho,
        'total': total,
        'enderecos': enderecos,
         'MERCADOPAGO_PUBLIC_KEY': settings.MERCADOPAGO_PUBLIC_KEY,  # ADICIONE ESTA LINHA
    })

@login_required
def adicionar_endereco_checkout(request):
    """View para adicionar endereço via AJAX no checkout"""
    if request.method == 'POST':
        try:
            rua = request.POST.get('rua')
            numero = request.POST.get('numero')
            complemento = request.POST.get('complemento', '')
            bairro = request.POST.get('bairro')
            cidade = request.POST.get('cidade')
            estado = request.POST.get('estado')
            cep = request.POST.get('cep')
            principal = request.POST.get('principal') == 'on'
            
            # Validações básicas
            if not all([rua, numero, bairro, cidade, estado, cep]):
                return JsonResponse({
                    'success': False, 
                    'error': 'Todos os campos obrigatórios devem ser preenchidos.'
                })
            
            # Se for definir como principal, remove principal de outros endereços
            if principal:
                EnderecoEntrega.objects.filter(usuario=request.user, principal=True).update(principal=False)
            
            # Criar novo endereço
            endereco = EnderecoEntrega(
                usuario=request.user,
                rua=rua,
                numero=numero,
                complemento=complemento,
                bairro=bairro,
                cidade=cidade,
                estado=estado,
                cep=cep,
                principal=principal
            )
            endereco.save()
            
            return JsonResponse({
                'success': True, 
                'endereco_id': endereco.id,
                'message': 'Endereço adicionado com sucesso!'
            })
            
        except Exception as e:
            print(f"Erro ao adicionar endereço: {str(e)}")
            return JsonResponse({
                'success': False, 
                'error': f'Erro ao adicionar endereço: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Método não permitido'})

@login_required
def excluir_endereco(request, endereco_id):
    """View para excluir endereço via AJAX"""
    if request.method == 'POST':
        try:
            endereco = get_object_or_404(EnderecoEntrega, id=endereco_id, usuario=request.user)
            endereco.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Endereço excluído com sucesso!'
            })
            
        except Exception as e:
            print(f"Erro ao excluir endereço: {str(e)}")
            return JsonResponse({
                'success': False, 
                'error': f'Erro ao excluir endereço: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Método não permitido'})

@login_required
def pagamento(request):
    # Buscar o último pedido pendente do usuário
    pedido = Pedido.objects.filter(usuario=request.user, status='pendente').last()
    
    if not pedido:
        messages.warning(request, 'Nenhum pedido pendente encontrado.')
        return redirect('pagina_inicial')
    
    return render(request, 'vendas/pagamento.html', {
        'pedido': pedido
    })

def criar_token_cartao_real(numero_cartao, mes_validade, ano_validade, cvv, nome_titular="Titular Cartão"):
    """
    Gera um token REAL para o cartão usando a API do Mercado Pago - CORRIGIDA
    """
    try:
        print("🔐 GERANDO TOKEN REAL DO CARTÃO...")
        print(f"💳 Cartão: **** **** **** {numero_cartao[-4:]}")
        print(f"📅 Validade: {mes_validade}/{ano_validade}")
        print(f"👤 Titular: {nome_titular}")
        
        # ⚠️ CORREÇÃO: Usar ACCESS TOKEN, não public key
        access_token = getattr(settings, 'MERCADOPAGO_ACCESS_TOKEN', None)
        if not access_token:
            print("❌ ERRO: Access Token não encontrado")
            return None
        
        print(f"🔑 Access Token: {access_token[:20]}...")
        
        # URL da API de tokens do Mercado Pago
        url = "https://api.mercadopago.com/v1/card_tokens"
        
        # Headers - ⚠️ CORREÇÃO: usar ACCESS TOKEN
        headers = {
            "Authorization": f"Bearer {access_token}",  # ✅ CORRIGIDO
            "Content-Type": "application/json",
            "User-Agent": "LojaPython/1.0"
        }
        
        # Dados do cartão
        payload = {
            "card_number": numero_cartao,
            "expiration_month": int(mes_validade),
            "expiration_year": int(ano_validade),
            "security_code": cvv,
            "cardholder": {
                "name": nome_titular
            }
        }
        
        print("📤 ENVIANDO PARA API DO MERCADO PAGO...")
        print(f"🔗 URL: {url}")
        print(f"📦 Payload: {payload}")
        
        # Fazer requisição com timeout
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"📡 RESPOSTA DA API: Status {response.status_code}")
        
        if response.status_code == 201:
            token_data = response.json()
            token = token_data.get("id")
            print(f"✅ TOKEN REAL GERADO COM SUCESSO: {token}")
            return token
        else:
            print(f"❌ ERRO NA TOKENIZAÇÃO: {response.status_code}")
            print(f"📋 Resposta completa: {response.text}")
            
            # Tentar extrair detalhes do erro
            try:
                error_details = response.json()
                print(f"🔍 Detalhes do erro: {error_details}")
                
                # Log mais detalhado para debugging
                if 'cause' in error_details:
                    for cause in error_details.get('cause', []):
                        print(f"🔍 Causa: {cause}")
                        
            except:
                print("🔍 Não foi possível ler detalhes do erro")
            
            return None
            
    except requests.exceptions.Timeout:
        print("⏰ TIMEOUT: A requisição demorou muito")
        return None
    except requests.exceptions.ConnectionError:
        print("🌐 ERRO DE CONEXÃO: Não foi possível conectar ao Mercado Pago")
        return None
    except Exception as e:
        print(f"💥 ERRO INESPERADO: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def criar_token_via_sdk(numero_cartao, mes_validade, ano_validade, cvv, nome_titular):
    """
    Método usando SDK do Mercado Pago
    """
    try:
        print("🔄 TENTANDO TOKENIZAÇÃO VIA SDK...")
        
        access_token = getattr(settings, 'MERCADOPAGO_ACCESS_TOKEN', None)
        if not access_token:
            print("❌ Access Token não configurado")
            return None
        
        # Configurar SDK
        sdk = mercadopago.SDK("TEST-60559e27-fc39-4003-bafb-21deba8799fe")
        
        # Dados do cartão
        card_data = {
            "card_number": numero_cartao,
            "expiration_month": int(mes_validade),
            "expiration_year": int(ano_validade),
            "security_code": cvv,
            "cardholder": {
                "name": nome_titular
            }
        }
        
        print("📤 CRIANDO TOKEN VIA SDK...")
        token_result = sdk.card_token().create(card_data)
        
        print(f"📡 RESPOSTA SDK: Status {token_result['status']}")
        
        if token_result["status"] in [200, 201]:
            token = token_result["response"]["id"]
            print(f"✅ TOKEN GERADO VIA SDK: {token}")
            return token
        else:
            print(f"❌ ERRO NA SDK: {token_result}")
            # Log detalhado do erro
            error_response = token_result.get('response', {})
            print(f"🔍 Detalhes do erro SDK: {error_response}")
            return None
            
    except Exception as e:
        print(f"💥 ERRO NA SDK: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

@login_required
def criar_pagamento(request):
    if request.method != 'POST':
        return JsonResponse({'erro': 'Método não permitido'}, status=405)
    
    try:
        data = json.loads(request.body)
        metodo = data.get('metodo')
        
        # Inicializar SDK do Mercado Pago
        sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
        
        if metodo == 'pix':
            payment_data = {
                "transaction_amount": float(data.get('total', 0)),
                "description": "Compra na Loja",
                "payment_method_id": "pix",
                "payer": {
                    "email": request.user.email,
                    "first_name": request.user.first_name,
                    "last_name": request.user.last_name,
                }
            }
            
            payment_response = sdk.payment().create(payment_data)
            payment = payment_response["response"]
            
            if payment['status'] == 'pending':
                return JsonResponse({
                    'status': 'pending',
                    'payment_id': payment['id'],
                    'qr_code': payment['point_of_interaction']['transaction_data']['qr_code'],
                    'qr_code_base64': payment['point_of_interaction']['transaction_data']['qr_code_base64']
                })
                
        elif metodo == 'cartao':
            payment_data = {
                "transaction_amount": float(data.get('transaction_amount', 0)),
                "token": data.get('token'),
                "description": "Compra na Loja",
                "installments": int(data.get('installments', 1)),
                "payment_method_id": data.get('paymentMethodId'),
                "issuer_id": data.get('issuerId'),
                "payer": {
                    "email": request.user.email,
                    "identification": {
                        "type": "CPF",
                        "number": "12345678909"  # Pegar do usuário
                    }
                }
            }
            
            payment_response = sdk.payment().create(payment_data)
            payment = payment_response["response"]
            
            return JsonResponse({
                'status': payment['status'],
                'payment_id': payment['id'],
                'pedido_id': 123  # ID do seu pedido
            })
            
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)
    
    return JsonResponse({'erro': 'Método de pagamento inválido'}, status=400)

   
@login_required
def processar_pagamento_cartao(request, pedido_id):
    if request.method != "POST":
        return JsonResponse({"erro": "Método não permitido."}, status=405)
    
    try:
        pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
        
        print(f"\n{'='*50}")
        print(f"🔐 Processando pagamento para pedido #{pedido.id}")
        print(f"{'='*50}")
        
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        print(f"📦 Dados recebidos: {data}")
        
        token = data.get('token')
        print(f"💳 Token: {token[:30] if token else 'NÃO FORNECIDO'}...")
        
        # VALOR MÍNIMO PARA TESTE
        transaction_amount = float(data.get("transaction_amount", pedido.total))
        print(f"💰 Valor: R$ {transaction_amount}")
        
        # Se o valor for muito baixo, usar um valor mínimo
        if transaction_amount < 5.00:
            print(f"⚠️ Valor muito baixo (R$ {transaction_amount}). Usando R$ 5.00 para teste.")
            transaction_amount = 5.00
        
        sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
        
        payment_data = {
            "transaction_amount": transaction_amount,
            "token": token,
            "description": f"Pedido #{pedido.id}",
            "installments": int(data.get("installments", 1)),
            "payment_method_id": data.get("payment_method_id"),
            "payer": {
                "email": data.get("payer", {}).get("email", request.user.email),
                "identification": {
                    "type": "CPF",
                    "number": data.get("payer", {}).get("identification", {}).get("number", "12345678909")
                }
            }
        }
        
        # issuer_id é opcional
        issuer_id = data.get("issuer_id")
        if issuer_id:
            payment_data["issuer_id"] = issuer_id
            print(f"🏦 Issuer ID: {issuer_id}")
        
        print(f"📤 Enviando para Mercado Pago: {json.dumps(payment_data, indent=2)}")
        
        payment_response = sdk.payment().create(payment_data)
        payment = payment_response["response"]
        
        print(f"📡 Resposta MP - Status: {payment.get('status')}")
        print(f"📡 Resposta completa: {json.dumps(payment, indent=2)}")
        
        # Se houve erro na API do MP
        if payment.get('status') in [400, '400'] or payment.get('error'):
            erro_msg = payment.get('message', 'Erro desconhecido')
            print(f"❌ ERRO MP: {erro_msg}")
            print(f"❌ Detalhes: {payment.get('cause', 'Sem detalhes')}")
            
            return JsonResponse({
                'status': 400,
                'message': erro_msg,
                'details': payment
            }, status=400)
        
        # Atualizar pedido
        pedido.pagamento_id = payment.get('id')
        pedido.status_pagamento = payment.get('status')
        
        if payment.get('status') == 'approved':
            pedido.status = 'pago'
        elif payment.get('status') == 'rejected':
            pedido.status = 'cancelado'
        
        pedido.save()
        
        return JsonResponse({
            'status': payment.get('status'),
            'payment_id': payment.get('id'),
            'message': payment.get('status_detail', ''),
            'pedido_id': pedido.id
        })
        
    except Exception as e:
        print(f"❌ EXCEÇÃO: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({"erro": str(e), "status": "error"}, status=500)

def detectar_bandeira(numero_cartao):
    """Detecta a bandeira do cartão baseado nos primeiros dígitos"""
    if not numero_cartao:
        return "visa"  # padrão
    
    primeiro_digito = numero_cartao[0]
    
    if primeiro_digito == '4':
        return "visa"
    elif primeiro_digito == '5':
        return "master"
    elif primeiro_digito == '3':
        return "amex"
    elif primeiro_digito == '6':
        return "elo"
    else:
        return "visa"  # padrão

@login_required
def verificar_credenciais_mp(request):
    """View para verificar se as credenciais do Mercado Pago estão funcionando"""
    access_token = getattr(settings, 'MERCADOPAGO_ACCESS_TOKEN', None)
    public_key = getattr(settings, 'MERCADOPAGO_PUBLIC_KEY', None)
    
    print("=== VERIFICAÇÃO DE CREDENCIAIS ===")
    print(f"Access Token: {access_token}")
    print(f"Public Key: {public_key}")
    
    if not access_token or not public_key:
        return JsonResponse({
            'status': 'error', 
            'message': 'Credenciais não configuradas'
        })
    
    # Testar conexão com a API
    try:
        sdk = mercadopago.SDK(access_token)
        
        # Tentar listar métodos de pagamento (endpoint simples)
        result = sdk.payment_methods().list()
        
        if result['status'] == 200:
            return JsonResponse({
                'status': 'success',
                'message': 'Credenciais válidas! Conexão estabelecida.',
                'payment_methods_count': len(result['response'])
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': f'Erro na API: {result}'
            })
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro de conexão: {str(e)}'
        })
    

# Detalhe do pedigo pago
@login_required
def detalhes_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
    itens_pedido = ItemPedido.objects.filter(pedido=pedido)
    
    return render(request, 'vendas/detalhes_pedido.html', {
        'pedido': pedido,
        'itens_pedido': itens_pedido
    })

@login_required
def processar_pagamento_pix(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
    
    print(f"=== INICIANDO PIX PARA PEDIDO {pedido.id} ===")
    
    from django.conf import settings
    
    access_token = getattr(settings, 'MERCADOPAGO_ACCESS_TOKEN', None)
    
    if not access_token:
        error_msg = "Access Token não encontrado no settings.py"
        context = {
            'pedido': pedido,
            'modo_desenvolvimento': True,
            'erro_exception': error_msg
        }
        return render(request, 'vendas/pagamento_pix.html', context)
    
    try:
        sdk = mercadopago.SDK(access_token)
        print("✅ SDK configurado")
        
        # DADOS MÍNIMOS PARA PIX - SEM notification_url
        payment_data = {
            "transaction_amount": float(pedido.total),
            "description": f"Pedido #{pedido.id}",
            "payment_method_id": "pix",
            "payer": {
                "email": request.user.email,
            },
            "external_reference": str(pedido.id),
        }
        
        print(f"📦 Dados do pagamento: {payment_data}")
        
        payment_response = sdk.payment().create(payment_data)
        print(f"📡 Resposta completa do MP: {payment_response}")
        
        if payment_response["status"] in [200, 201]:
            payment = payment_response["response"]
            print(f"✅ Pagamento criado! ID: {payment['id']}")
            
            # Salvar ID no pedido
            pedido.id_mercado_pago = payment["id"]
            pedido.save()
            print(f"✅ ID salvo no pedido: {pedido.id_mercado_pago}")
            
            # Verificar se tem dados do PIX
            if 'point_of_interaction' in payment and 'transaction_data' in payment['point_of_interaction']:
                pix_data = payment['point_of_interaction']['transaction_data']
                
                context = {
                    'pedido': pedido,
                    'modo_desenvolvimento': False,
                    'qr_code': pix_data.get('qr_code', ''),
                    'qr_code_base64': pix_data.get('qr_code_base64', ''),
                    'ticket_url': pix_data.get('ticket_url', ''),
                    'mp_public_key': getattr(settings, 'MERCADOPAGO_PUBLIC_KEY', ''),
                }
                
                print("🎉 PIX criado com sucesso!")
                return render(request, 'vendas/pagamento_pix.html', context)
            else:
                raise Exception("Dados do PIX não encontrados na resposta")
        else:
            error_details = payment_response.get('response', {})
            error_msg = f"Erro MP - Status {payment_response['status']}: {error_details}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
            
    except Exception as e:
        error_msg = f"Erro ao criar PIX: {str(e)}"
        print(f"💥 {error_msg}")
        
        context = {
            'pedido': pedido,
            'modo_desenvolvimento': True,
            'erro_exception': error_msg
        }
        return render(request, 'vendas/pagamento_pix.html', context)

# webhooks para receber confirmações de pagamento:   
    
@csrf_exempt  # Remove CSRF para webhook externo
def webhook_mercadopago(request):
    """
    Webhook para receber notificações do Mercado Pago
    IMPORTANTE: CSRF está desabilitado pois é chamado externamente
    """
    if request.method == 'POST':
        try:
            # Log para debug
            print("=== WEBHOOK MERCADO PAGO RECEBIDO ===")
            print("Headers:", dict(request.headers))
            
            # Verificar se é um payload JSON
            if request.content_type == 'application/json':
                data = json.loads(request.body.decode('utf-8'))
            else:
                data = request.POST.dict()
            
            print("Dados recebidos:", data)
            
            # Extrair ID do pagamento
            payment_id = None
            if 'data' in data and 'id' in data['data']:
                payment_id = data['data']['id']
            elif 'id' in data:
                payment_id = data['id']
            
            print(f"Payment ID recebido: {payment_id}")
            
            if payment_id:
                # Buscar pedido pelo ID do Mercado Pago
                pedido = Pedido.objects.filter(id_mercado_pago=payment_id).first()
                
                if pedido:
                    print(f"Pedido encontrado: #{pedido.id}")
                    # Consultar status atual no Mercado Pago
                    return atualizar_status_pedido(pedido)
                else:
                    print(f"Pedido não encontrado para payment_id: {payment_id}")
                    return JsonResponse({'status': 'not_found'}, status=404)
            else:
                print("Nenhum payment_id encontrado no webhook")
                return JsonResponse({'status': 'invalid_data'}, status=400)
                
        except Exception as e:
            print(f"💥 ERRO NO WEBHOOK: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'invalid_method'}, status=405)

def atualizar_status_pedido(pedido):
    try:
        sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
        payment_info = sdk.payment().get(pedido.id_mercado_pago)

        if payment_info['status'] == 200:
            payment = payment_info['response']
            status_mp = payment['status']

            status_map = {
                'pending': 'pendente',
                'approved': 'aprovado',
                'rejected': 'rejeitado',
                'cancelled': 'rejeitado'
            }

            novo_status_pagamento = status_map.get(status_mp, 'pendente')

            if pedido.status_pagamento != novo_status_pagamento:
                pedido.status_pagamento = novo_status_pagamento

                if novo_status_pagamento == 'aprovado':
                    pedido.data_pagamento = timezone.now()

                    # 🔥 IMPORTANTE: inicia fluxo logístico
                    pedido.status_entrega = 'preparando'

                    CarrinhoItem.objects.filter(usuario=pedido.usuario).delete()

                pedido.save()

        return True

    except Exception as e:
        print(f"Erro: {e}")
        return False


@login_required
def diagnostico_pagamento(request, pedido_id):
    """Página de diagnóstico para verificar status do pagamento"""
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
    
    # Consultar status diretamente no Mercado Pago
    status_info = {}
    try:
        sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
        payment_info = sdk.payment().get(pedido.id_mercado_pago)
        
        if payment_info['status'] == 200:
            payment = payment_info['response']
            status_info = {
                'status_mp': payment['status'],
                'status_detail': payment.get('status_detail', ''),
                'date_approved': payment.get('date_approved', ''),
                'external_reference': payment.get('external_reference', ''),
                'order_id': payment.get('order', {}).get('id', ''),
            }
    except Exception as e:
        status_info['erro'] = str(e)
    
    context = {
        'pedido': pedido,
        'status_info': status_info,
        'webhook_url': f"{settings.SITE_URL}/webhook/mercadopago/",
    }
    
    return render(request, 'vendas/diagnostico_pagamento.html', context)    
    
# views.py - Views de callback para redirecionamento após pagamento
@login_required
def pagamento_sucesso(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)

    if pedido.status_pagamento != 'aprovado':
        pedido.status_pagamento = 'aprovado'
        pedido.status = 'aprovado'  # ✅ corrigido
        pedido.save()

    CarrinhoItem.objects.filter(usuario=request.user).delete()

    return render(request, 'vendas/pagamento_sucesso.html', {'pedido': pedido})

@login_required
def pagamento_falha(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)

    pedido.status_pagamento = 'rejeitado'  # melhor que "cancelado"
    pedido.status = 'cancelado'  # ✅ corrigido
    pedido.save()

    return render(request, 'vendas/pagamento_falha.html', {'pedido': pedido})

@login_required
def pagamento_pendente(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)

    pedido.status_pagamento = 'pendente'
    pedido.status = 'pendente'
    pedido.save()

    return render(request, 'vendas/pagamento_pendente.html', {'pedido': pedido})    

@staff_member_required
def atualizar_status_entrega(request, pedido_id):
    if request.method == 'POST':
        pedido = get_object_or_404(Pedido, id=pedido_id)

        novo_status = request.POST.get('status_entrega')
        pedido.status_entrega = novo_status
        pedido.save()

        return redirect('gerenciar_pedidos')

    return redirect('gerenciar_pedidos')

# Views lista todos pedidos

@login_required
def gerenciar_pedidos(request):
    if not request.user.is_superuser:
        return redirect('pagina_inicial')

    pedidos = Pedido.objects.all().order_by('-id')

    return render(request, 'vendas/admin/pedidos.html', {
        'pedidos': pedidos
    })

@login_required
def verificar_status_pagamento(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)

    if not pedido.id_mercado_pago:
        return JsonResponse({'status': 'error'})

    atualizar_status_pedido(pedido)

    return JsonResponse({
        'status': 'success',
        'status_pagamento': pedido.status_pagamento,
        'status_entrega': pedido.status_entrega
    })

# Função para verificar se o usuário é superusuário
def superuser_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Você precisa estar logado para acessar esta página.')
            return redirect('login')
        if not request.user.is_superuser:
            messages.error(request, 'Acesso restrito apenas para administradores.')
            return redirect('pagina_inicial')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@superuser_required
def estoque(request):
    # [código existente permanece o mesmo]
    # Obter parâmetros de filtro
    status_filter = request.GET.get('status')
    categoria_filter = request.GET.get('categoria')
    estoque_baixo_filter = request.GET.get('estoque_baixo')
    
    # Query base
    produtos = Produto.objects.all()
    
    # Aplicar filtros
    if status_filter == 'ativo':
        produtos = produtos.filter(ativo=True)
    elif status_filter == 'inativo':
        produtos = produtos.filter(ativo=False)
    
    if categoria_filter:
        produtos = produtos.filter(categoria=categoria_filter)
    
    if estoque_baixo_filter == 'sim':
        produtos = produtos.filter(quantidade_estoque__lte=5)
    elif estoque_baixo_filter == 'nao':
        produtos = produtos.filter(quantidade_estoque__gt=5)
    
    # Estatísticas
    total_produtos = Produto.objects.count()
    produtos_ativos = Produto.objects.filter(ativo=True).count()
    produtos_inativos = Produto.objects.filter(ativo=False).count()
    total_estoque = Produto.objects.aggregate(Sum('quantidade_estoque'))['quantidade_estoque__sum'] or 0
    
    context = {
        'produtos': produtos,
        'total_produtos': total_produtos,
        'produtos_ativos': produtos_ativos,
        'produtos_inativos': produtos_inativos,
        'total_estoque': total_estoque,
    }
    
    return render(request, 'vendas/estoque.html', context)

@superuser_required
@login_required
def editar_produto(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)
    if request.method == 'POST':
        form = ProdutoForm(request.POST, request.FILES, instance=produto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Produto atualizado com sucesso!')
            return redirect('estoque')
    else:
        form = ProdutoForm(instance=produto)
    return render(request, 'vendas/estoque.html', {'form': form, 'produto': produto})

@superuser_required
@login_required
def excluir_produto(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)
    if request.method == 'POST':
        produto.delete()
        messages.success(request, 'Produto excluído com sucesso!')
        return redirect('lista_produto')
    return render(request, 'vendas/excluir_produto.html', {'produto': produto})

@superuser_required
@login_required
def cadastrar_produto(request):
    if request.method == 'POST':
        form = ProdutoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Produto cadastrado com sucesso!')
            return redirect('estoque')
    else:
        form = ProdutoForm()

    return render(request, 'vendas/cadastrar_produto.html', {'form': form})

def meus_pedidos(request):
    pedidos = Pedido.objects.filter(usuario=request.user)\
        .prefetch_related('itens_pedido__produto')\
        .order_by('-data_criacao')

    return render(request, 'vendas/meus_pedidos.html', {
        'pedidos': pedidos
    })

# Página inicial
def pagina_inicial(request):
    
    criar_admin()

    categoria_selecionada = request.GET.get('categoria', '')
    
    if categoria_selecionada:
        produtos = Produto.objects.filter(categoria=categoria_selecionada)
    else:
        produtos = Produto.objects.all()

    # Montar lista com preços calculados
    produtos_com_precos = []
    for p in produtos:
        preco_pix = (p.preco * Decimal("0.90")).quantize(Decimal("0.01"))  # 10% OFF no pix
        preco_parcela = (p.preco / Decimal("3")).quantize(Decimal("0.01")) # parcelado em 3x
        produtos_com_precos.append({
            "id": p.id,
            "nome": p.nome,
            "preco": p.preco,
            "preco_pix": preco_pix,
            "preco_parcela": preco_parcela,
            "imagem": p.imagem,
            "categoria": p.categoria,
        })

    context = {
        'produtos': produtos_com_precos,
        'categoria_selecionada': categoria_selecionada
    }
    return render(request, 'vendas/index.html', context)

@login_required
def lista_vendas(request):
    vendas = Venda.objects.all().order_by('-data_venda')
    produtos = Produto.objects.all()
    return render(request, 'vendas/lista_vendas.html', {'vendas': vendas, 'produtos': produtos})

@login_required
def nova_venda(request):
    if request.method == 'POST':
        form = VendaForm(request.POST)
        if form.is_valid():
            venda = form.save(commit=False)
            venda.vendedor = request.user
            venda.preco_unitario = venda.produto.preco
            venda.save()
            messages.success(request, 'Venda registrada com sucesso!')
            return redirect('lista_vendas')
    else:
        form = VendaForm()

    produtos = Produto.objects.all()
    return render(request, 'vendas/nova_venda.html', {'form': form, 'produtos': produtos})

@login_required
def relatorios(request):
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')

    vendas = Venda.objects.select_related('produto')

    if data_inicio:
        data_inicio = parse_date(data_inicio)
        vendas = vendas.filter(data_venda__date__gte=data_inicio)

    if data_fim:
        data_fim = parse_date(data_fim)
        vendas = vendas.filter(data_venda__date__lte=data_fim)

    produtos_vendidos = vendas.values('produto__nome').annotate(total=Sum('quantidade'))
    total_vendas = vendas.count()
    valor_total = vendas.aggregate(total=Sum(F('quantidade') * F('preco_unitario')))['total'] or 0

    return render(request, 'vendas/relatorios.html', {
        'produtos_vendidos': produtos_vendidos,
        'data_inicio': request.GET.get('data_inicio', ''),
        'data_fim': request.GET.get('data_fim', ''),
        'total_vendas': total_vendas,
        'valor_total': valor_total,
    })

@login_required
def editar_venda(request, venda_id):
    venda = get_object_or_404(Venda, id=venda_id)

    if request.method == 'POST':
        form = VendaForm(request.POST, instance=venda)
        if form.is_valid():
            form.save()
            return redirect('lista_vendas')
    else:
        form = VendaForm(instance=venda)

    return render(request, 'vendas/editar_venda.html', {'form': form})

@login_required
def atualizar_venda(request, venda_id):
    if request.method == 'POST':
        venda = get_object_or_404(Venda, id=venda_id)
        produto_id = request.POST.get('produto_id')
        quantidade = request.POST.get('quantidade')

        if produto_id and quantidade:
            venda.produto_id = produto_id
            venda.quantidade = int(quantidade)
            venda.total = venda.quantidade * venda.preco_unitario
            venda.save()

    return redirect('lista_vendas')

# Registrar Usuário
def registrar_usuario(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuário criado com sucesso! Faça login.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'vendas/registrar.html', {'form': form})

def registrar_com_endereco(request):
    # Verifica se tem email na session
    email = request.session.get('email_cadastro')
    print("DEBUG - Email na session:", email)
    if not email:
        messages.warning(request, 'Por favor, informe seu e-mail primeiro')
        return redirect('login')
    
    if request.method == 'POST':
        try:
            # Dados do formulário
            nome = request.POST.get('nome')
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            cpf = request.POST.get('cpf')
            celular = request.POST.get('celular')
            
            # Dados do endereço
            cep = request.POST.get('cep')
            rua = request.POST.get('rua')
            numero = request.POST.get('numero')
            complemento = request.POST.get('complemento', '')
            bairro = request.POST.get('bairro')
            cidade = request.POST.get('cidade')
            estado = request.POST.get('estado')
            
            # Validações
            if password1 != password2:
                messages.error(request, 'As senhas não coincidem')
                return redirect('registrar_com_endereco')
            
            # Cria o usuário
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password1,
                first_name=nome
            )
            
            # Cria o endereço
            endereco = EnderecoEntrega(
                usuario=user,
                cep=cep,
                rua=rua,
                numero=numero,
                complemento=complemento,
                bairro=bairro,
                cidade=cidade,
                estado=estado,
                principal=True
            )
            endereco.save()
            
            # Faz login automático
            user = authenticate(username=email, password=password1)
            if user:
                login(request, user)
                # Limpa a session
                if 'email_cadastro' in request.session:
                    del request.session['email_cadastro']
                
                messages.success(request, 'Conta criada com sucesso!')
                return redirect('visualizar_carrinho')
                
        except IntegrityError:
            messages.error(request, 'Este e-mail já está cadastrado')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Erro ao criar conta: {str(e)}')
    
    return render(request, 'vendas/registrar_com_endereco.html', {
        'email': email
    })

def login_view(request):
    if request.method == 'POST':
        print("DEBUG - POST data:", request.POST)  # Para ver o que está chegando
        
        # Verifica se é login normal
        if 'username' in request.POST:
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                return redirect('index')
            else:
                messages.error(request, 'E-mail ou senha inválidos')
                
        # Verifica se é para criar conta
        elif 'email' in request.POST:
            email = request.POST.get('email')
            print("DEBUG - Email recebido:", email)  # Debug
            
            if email:
                # SALVA na session CORRETAMENTE
                request.session['email_cadastro'] = email
                request.session.modified = True  # Força a salvar a session
                print("DEBUG - Email salvo na session:", request.session.get('email_cadastro'))
                return redirect('registrar_com_endereco')
            else:
                messages.error(request, 'Por favor, informe um e-mail válido')
    
    return render(request, 'vendas/login.html')

def solicitar_orcamento(request):
    if request.method == 'POST':
        form = OrcamentoForm(request.POST)
        if form.is_valid():
            nome = form.cleaned_data['nome']
            telefone = form.cleaned_data['telefone']
            ambiente = dict(form.fields['ambiente'].choices)[form.cleaned_data['ambiente']]
            orcamento = dict(form.fields['orcamento'].choices)[form.cleaned_data['orcamento']]
            mensagem = f"""*SOLICITAÇÃO DE ORÇAMENTO*

*Nome:* {nome}
*Telefone:* {telefone}
*Ambiente a ser planejado:* {ambiente}
*Faixa de orçamento:* {orcamento}

Por favor, entre em contato para discutir este projeto."""
            return JsonResponse({'mensagem': mensagem})
        else:
            return JsonResponse({'errors': form.errors}, status=400)
    else:
        form = OrcamentoForm()
    return render(request, 'vendas/orcamento.html', {'form': form})

