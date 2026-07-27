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

from django.forms import inlineformset_factory

from collections import OrderedDict
from django.http import HttpResponseBadRequest
from django.views.decorators.http import require_POST
from vendas.models import Produto, ProdutoVariacao, Venda, CarrinhoItem, EnderecoEntrega, Pedido, ItemPedido, COR_CHOICES, TAMANHO_CHOICES
from vendas.forms import VendaForm, ProdutoForm, ProdutoVariacaoForm, ProdutoVariacaoInlineFormSet, UsuarioComEnderecoForm
from vendas.forms import OrcamentoForm  # ← Verifique esta importação
import json, os
import requests
import mercadopago
from django.conf import settings


from vendas.utils import get_itens_carrinho







# vendas/views/views.py

def calcular_precos(produto_list):
    """Calcula preços para uma lista de produtos (usa primeira variação)"""
    resultado = []
    for p in produto_list:
        # Buscar a primeira variação do produto
        variacao = p.variacoes.first()
        if variacao:
            preco_pix = (variacao.preco * Decimal("0.90")).quantize(Decimal("0.01"))
            preco_parcela = (variacao.preco / Decimal("3")).quantize(Decimal("0.01"))
            resultado.append({
                "id": p.id,
                "nome": p.nome,
                "preco": variacao.preco,
                "preco_pix": preco_pix,
                "preco_parcela": preco_parcela,
                "imagem": p.imagem or (variacao.imagem if variacao.imagem else None),
                "categoria": p.categoria,
            })
    return resultado


# vendas/views/views.py

def pagina_inicial(request):
    categoria_selecionada = request.GET.get('categoria', '')
    
    # Query base
    produtos_query = Produto.objects.filter(ativo=True)
    
    if categoria_selecionada:
        produtos = produtos_query.filter(categoria=categoria_selecionada)
    else:
        produtos = produtos_query
    
    # Separar produtos por categoria
    produtos_lancamentos = produtos_query.filter(categoria='lancamentos')[:12]
    produtos_promocoes = produtos_query.filter(categoria='promocoes')[:12]
    produtos_conjuntos = produtos_query.filter(categoria='conjuntos')[:12]
    produtos_outros = produtos_query.filter(categoria='outros')[:12]
    produtos_destaque = produtos_query.order_by('-data_cadastro')[:6]
    
    # Calcular preços a partir da primeira variação
    def calcular_precos(produto_list):
        resultado = []
        for p in produto_list:
            variacao = p.variacoes.first()
            if not variacao:
                continue
            
            preco_pix = (variacao.preco * Decimal("0.90")).quantize(Decimal("0.01"))
            preco_parcela = (variacao.preco / Decimal("3")).quantize(Decimal("0.01"))
            
            imagem_url = None
            if variacao.imagem:
                try:
                    imagem_url = variacao.imagem.url.replace("http://", "https://")
                except:
                    imagem_url = None
            if not imagem_url and p.imagem:
                try:
                    imagem_url = p.imagem.url.replace("http://", "https://")
                except:
                    imagem_url = None
            if not imagem_url:
                imagem_url = 'https://placehold.co/300x200?text=Sem+Imagem'
            
            resultado.append({
                "id": p.id,
                "nome": p.nome,
                "preco": variacao.preco,
                "preco_pix": preco_pix,
                "preco_parcela": preco_parcela,
                "imagem": imagem_url,
                "categoria": p.categoria,
            })
        return resultado
    
    context = {
        'produtos_lancamentos': calcular_precos(produtos_lancamentos),
        'produtos_promocoes': calcular_precos(produtos_promocoes),
        'produtos_conjuntos': calcular_precos(produtos_conjuntos),
        'produtos_outros': calcular_precos(produtos_outros),
        'produtos_destaque': calcular_precos(produtos_destaque),
        'categoria_selecionada': categoria_selecionada,
        'produtos': calcular_precos(produtos),
    }
    
    return render(request, 'vendas/index.html', context)

#teste

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


from decimal import Decimal
from collections import OrderedDict
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from ..models import Produto, ProdutoVariacao, TAMANHO_CHOICES  # 🔥 IMPORTE A CONSTANTE

def detalhes_produto(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id, ativo=True)
    
    # Buscar variações disponíveis
    variacoes = produto.variacoes.all()
    
    if not variacoes.exists():
        messages.warning(request, 'Este produto não está disponível no momento.')
        return redirect('pagina_inicial')
    
    # 🔥 ORGANIZAR CORES E TAMANHOS POR COR
    colors = OrderedDict()
    sizes_by_color = {}
    
    for var in variacoes:
        cor = var.cor
        if cor not in colors:
            imagem_url = None
            if var.imagem:
                try:
                    imagem_url = var.imagem.url.replace("http://", "https://")
                except:
                    imagem_url = None
            
            colors[cor] = {
                'cor': cor,
                'cor_display': cor,
                'imagem': imagem_url
            }
            sizes_by_color[cor] = []
        if var.tamanho not in sizes_by_color[cor]:
            sizes_by_color[cor].append(var.tamanho)
    
    # 🔥 LISTA DE TAMANHOS (TODOS OS POSSÍVEIS) - CORRIGIDO
    # Usa a constante importada do models.py
    TAMANHO_CHOICES_DICT = dict(TAMANHO_CHOICES)  # Agora TAMANHO_CHOICES é a constante do models.py
    tamanhos_disponiveis = []
    for val, label in TAMANHO_CHOICES_DICT.items():
        # Verifica se o tamanho existe em alguma cor
        existe = any(val in sizes for sizes in sizes_by_color.values())
        tamanhos_disponiveis.append({
            'valor': val,
            'label': label,
            'disponivel': existe
        })
    
    # --- PREÇOS ---
    primeira_variacao = variacoes.first()
    preco = primeira_variacao.preco
    preco_pix = preco * Decimal("0.90")
    preco_parcela = preco / Decimal("3")
    
    context = {
        'produto': produto,
        'variacoes': variacoes,
        'preco': preco,
        'preco_pix': preco_pix.quantize(Decimal("0.01")),
        'preco_parcela': preco_parcela.quantize(Decimal("0.01")),
        'cores_com_imagem': list(colors.values()),
        'tamanhos_disponiveis': tamanhos_disponiveis,
        'sizes_by_color': sizes_by_color,  # 🔥 PARA O JAVASCRIPT
        'size_labels': TAMANHO_CHOICES_DICT,  # 🔥 PARA O JAVASCRIPT
        'primeira_variacao': primeira_variacao,
    }
    return render(request, 'vendas/detalhes_produto.html', context)



def adicionar_carrinho(request, produto_id):
    if request.method == 'POST':
        produto = get_object_or_404(Produto, id=produto_id)

        try:
            quantidade = int(request.POST.get('quantidade', 1))
        except:
            quantidade = 1

        cor = request.POST.get('cor', '').strip()
        tamanho = request.POST.get('tamanho', '').strip()
        action = request.POST.get('action', 'carrinho')

        # Buscar a variação específica
        from ..models import ProdutoVariacao
        
        if not cor or not tamanho:
            variacao = produto.variacoes.first()
            if not variacao:
                messages.error(request, 'Este produto não está disponível.')
                return redirect('pagina_inicial')
        else:
            try:
                variacao = ProdutoVariacao.objects.get(
                    produto=produto,
                    cor=cor,
                    tamanho=tamanho
                )
            except ProdutoVariacao.DoesNotExist:
                messages.error(request, 'Produto não disponível nas opções selecionadas')
                return redirect('detalhes_produto', produto_id=produto_id)
        
        # Verificar estoque
        if variacao.quantidade_estoque < quantidade:
            messages.error(request, f'Quantidade indisponível. Estoque: {variacao.quantidade_estoque}')
            return redirect('detalhes_produto', produto_id=produto_id)
        
        # ===== SE NÃO ESTÁ LOGADO =====
        if not request.user.is_authenticated:
            carrinho = request.session.get('carrinho', {})
            
            if action == 'comprar':
                carrinho = {}
            
            # Chave única para a variação
            produto_key = f"v_{variacao.id}"
            
            if produto_key in carrinho:
                carrinho[produto_key]['quantidade'] += quantidade
            else:
                carrinho[produto_key] = {
                    'variacao_id': variacao.id,
                    'produto_nome': produto.nome,
                    'cor': variacao.cor,
                    'tamanho': variacao.tamanho,
                    'preco': float(variacao.preco),
                    'quantidade': quantidade,
                    'imagem': variacao.imagem.url if variacao.imagem else None
                }
            
            # 🔥 SALVA EM AMBOS OS LUGARES
            request.session['carrinho'] = carrinho
            request.session['carrinho_persistente'] = carrinho
            request.session.modified = True
            request.session.save()
            
            print(f"🛒 CARRINHO SALVO (adicionar_carrinho): {carrinho}")
            
            if action == 'comprar':
                return redirect('login')
            else:
                messages.success(request, f'{produto.nome} ({variacao.cor}/{variacao.tamanho}) adicionado!')
                return redirect('detalhes_produto', produto_id=produto_id)

        # ===== SE ESTÁ LOGADO =====
        if action == 'comprar':
            CarrinhoItem.objects.filter(usuario=request.user).delete()
        
        item, created = CarrinhoItem.objects.get_or_create(
            usuario=request.user,
            variacao=variacao,
            defaults={'quantidade': quantidade}
        )
        
        if not created:
            item.quantidade += quantidade
            item.save()
        
        messages.success(request, f'{produto.nome} ({variacao.cor}/{variacao.tamanho}) adicionado!')
        
        if action == 'comprar':
            return redirect('checkout')
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



def visualizar_carrinho(request):
    """Exibe o carrinho (funciona para logados e anônimos)"""
    
    # 🔥 TENTA BUSCAR O CARRINHO DE VÁRIOS LUGARES
    carrinho = request.session.get('carrinho_persistente', {})
    if not carrinho:
        carrinho = request.session.get('carrinho', {})
    
    print(f"🛒 CARRINHO EM visualizar_carrinho: {carrinho}")
    print(f"🛒 SESSÃO COMPLETA: {dict(request.session)}")
    
    itens = []
    total = 0
    total_itens = 0
    
    for chave, item in carrinho.items():
        if not isinstance(item, dict):
            continue
        
        quantidade = item.get('quantidade', 1)
        preco = item.get('preco', 0)
        subtotal = quantidade * preco
        total += subtotal
        total_itens += quantidade
        
        # Busca a variação para verificar estoque
        try:
            variacao = ProdutoVariacao.objects.get(id=item.get('variacao_id'))
            estoque_disponivel = variacao.quantidade_estoque
            nome = variacao.produto.nome
        except ProdutoVariacao.DoesNotExist:
            estoque_disponivel = 0
            nome = item.get('produto_nome', 'Produto')
        
        itens.append({
            'chave': chave,
            'id': item.get('id'),
            'variacao_id': item.get('variacao_id'),
            'produto_id': item.get('produto_id'),
            'nome': nome,
            'quantidade': quantidade,
            'preco': preco,
            'cor': item.get('cor', 'Branco'),
            'tamanho': item.get('tamanho', 'M'),
            'imagem': item.get('imagem'),
            'subtotal': subtotal,
            'estoque_disponivel': estoque_disponivel,
        })
    
    context = {
        'itens_carrinho': itens,
        'total': total,
        'total_itens': total_itens,
        'carrinho_vazio': len(itens) == 0,
    }
    return render(request, 'vendas/carrinho.html', context)


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
@login_required
def comprar_agora(request, produto_id):
    if request.method == 'POST':
        produto = get_object_or_404(Produto, id=produto_id, ativo=True)
        quantidade = int(request.POST.get('quantidade', 1))
        cor = request.POST.get('cor', '').strip()
        tamanho = request.POST.get('tamanho', '').strip()
        
        # 🔥 Busca a variação específica
        if not cor or not tamanho:
            messages.error(request, 'Selecione cor e tamanho do produto.')
            return redirect('detalhes_produto', produto_id=produto_id)
        
        from ..models import ProdutoVariacao
        variacao = ProdutoVariacao.objects.filter(
            produto=produto,
            cor=cor,
            tamanho=tamanho
        ).first()
        
        if not variacao:
            messages.error(request, 'Variação do produto não encontrada.')
            return redirect('detalhes_produto', produto_id=produto_id)
        
        # 🔥 Usuário logado: salva no BANCO (usando variacao)
        # Limpa o carrinho anterior
        CarrinhoItem.objects.filter(usuario=request.user).delete()
        
        # Cria o novo item usando a variação
        CarrinhoItem.objects.create(
            usuario=request.user,
            variacao=variacao,  # ← USA A VARIAÇÃO!
            quantidade=quantidade
        )
        
        messages.success(request, f'{produto.nome} ({cor}/{tamanho}) adicionado ao carrinho!')
        return redirect('visualizar_carrinho')
    
    return redirect('detalhes_produto', produto_id=produto_id)



def comprar_agora_anonimo(request, produto_id):
    """Para usuários não logados - salva produto na sessão e redireciona para login"""
    produto = get_object_or_404(Produto, id=produto_id)
    
    quantidade = int(request.GET.get('quantidade', 1))
    cor = request.GET.get('cor', '').strip()
    tamanho = request.GET.get('tamanho', '').strip()
    
    # Buscar a variação
    variacao = ProdutoVariacao.objects.filter(
        produto=produto,
        cor=cor,
        tamanho=tamanho
    ).first()
    
    if not variacao:
        messages.error(request, 'Variação do produto não encontrada.')
        return redirect('detalhes_produto', produto_id=produto_id)
    
    # 🔥 CRIA O CARRINHO NA SESSÃO
    carrinho = {}
    chave = f"variacao_{variacao.id}"
    
    carrinho[chave] = {
        'variacao_id': variacao.id,
        'produto_id': produto.id,  # 🔥 ADICIONAR PARA FALLBACK
        'nome': produto.nome,
        'quantidade': quantidade,
        'preco': float(variacao.preco),
        'cor': cor,
        'tamanho': tamanho,
        'imagem': variacao.imagem.url if variacao.imagem else None
    }
    
    # 🔥 SALVA NA SESSÃO E GARANTE QUE FOI SALVO
    request.session['carrinho'] = carrinho
    request.session.modified = True
    request.session.save()
    
    print(f"🛒 CARRINHO SALVO NA SESSÃO: {carrinho}")
    print(f"🛒 SESSÃO COMPLETA: {dict(request.session)}")
    
    messages.info(request, 'Produto adicionado ao carrinho! Faça login para finalizar.')
    
    if request.GET.get('email'):
        request.session['email_cadastro'] = request.GET.get('email')
    
    return redirect(f'{settings.LOGIN_URL}?next=/carrinho/')
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
        'itens_pedido__variacao',  # ← BUSCA A VARIAÇÃO
        'itens_pedido__variacao__produto'  # ← BUSCA O PRODUTO ATRAVÉS DA VARIAÇÃO
    )

    for pedido in pedidos:
        status = pedido.status
        status_entrega = pedido.status_entrega

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
    
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if request.method == 'POST':
        print("=== DADOS RECEBIDOS NO POST ===")
        print("endereco_id:", request.POST.get('endereco_id'))
        print("metodo_pagamento:", request.POST.get('metodo_pagamento'))
        print("tipo_entrega:", request.POST.get('tipo_entrega'))
        print("is_ajax:", is_ajax)
        
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
            
            from decimal import Decimal
            frete = Decimal('15.00') if tipo_entrega == 'entrega' else Decimal('0.00')
            total_com_frete = total + frete
            
            if metodo_pagamento == 'pix':
                total_com_frete = total_com_frete * Decimal('0.90')
            
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
            
            # 🔥 CRIAR ITENS DO PEDIDO USANDO VARIAÇÃO
            for item_carrinho in itens_carrinho:
                if not item_carrinho.variacao:
                    print(f"⚠️ Item sem variação: {item_carrinho.id}")
                    continue
                
                ItemPedido.objects.create(
                    pedido=pedido,
                    variacao=item_carrinho.variacao,  # ← USA A VARIAÇÃO
                    quantidade=item_carrinho.quantidade,
                    preco_unitario=item_carrinho.variacao.preco  # ← PREÇO DA VARIAÇÃO
                )
                print(f"Item adicionado: {item_carrinho.variacao.produto.nome} - {item_carrinho.variacao.cor}/{item_carrinho.variacao.tamanho}")
            
            # Limpar carrinho
            itens_carrinho.delete()
            
            if metodo_pagamento == 'pix':
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'pedido_id': pedido.id,
                        'metodo': 'pix',
                        'redirect_url': reverse('processar_pagamento_pix', args=[pedido.id])
                    })
                else:
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
                    return redirect('processar_pagamento_cartao', pedido_id=pedido.id)
            
        except Exception as e:
            print(f"ERRO: {str(e)}")
            import traceback
            traceback.print_exc()
            
            if is_ajax:
                return JsonResponse({'erro': str(e)}, status=500)
            messages.error(request, f'Erro ao processar pedido: {str(e)}')
            return redirect('checkout')
    
    # 🔥 PREPARAR ITENS PARA O TEMPLATE (com cor/tamanho da variação)
    itens_para_template = []
    for item in itens_carrinho:
        if item.variacao:
            itens_para_template.append({
                'id': item.id,
                'produto': item.variacao.produto,  # ← Produto
                'variacao': item.variacao,  # ← Variação
                'quantidade': item.quantidade,
                'cor_selecionada': item.variacao.cor,  # ← COR DA VARIAÇÃO
                'tamanho_selecionado': item.variacao.tamanho,  # ← TAMANHO DA VARIAÇÃO
                'subtotal': item.subtotal,
                'imagem': item.variacao.imagem.url if item.variacao.imagem else None,
            })
    
    return render(request, 'vendas/checkout.html', {
        'itens_carrinho': itens_para_template,  # ← DADOS CORRETOS
        'total': total,
        'enderecos': enderecos,
        'MERCADOPAGO_PUBLIC_KEY': settings.MERCADOPAGO_PUBLIC_KEY,
    })


@login_required
#def excluir_endereco(request, endereco_id):
   
   

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
        pedido.status = 'aprovado'  # ✅ mantido
        # 🔥 CORRIGIDO: define status_entrega para 'preparando'
        pedido.status_entrega = 'preparando'
        pedido.save()

    CarrinhoItem.objects.filter(usuario=request.user).delete()

    return render(request, 'vendas/pagamento_sucesso.html', {'pedido': pedido})

@login_required
def pagamento_falha(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)

    pedido.status_pagamento = 'rejeitado'
    pedido.status = 'cancelado'
    pedido.status_entrega = 'cancelado'  # ✅ Adicionado
    pedido.save()

    return render(request, 'vendas/pagamento_falha.html', {'pedido': pedido})

@login_required
def pagamento_pendente(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)

    pedido.status_pagamento = 'pendente'
    pedido.status = 'pendente'
    pedido.status_entrega = 'aguardando'  # ✅ Adicionado
    pedido.save()

    return render(request, 'vendas/pagamento_pendente.html', {'pedido': pedido})
    
@staff_member_required
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
                    # 🔥 CORRIGIDO: define status_entrega corretamente
                    pedido.status_entrega = 'preparando'
                    pedido.status = 'aprovado'  # ✅ Adicionado
                    CarrinhoItem.objects.filter(usuario=pedido.usuario).delete()
                elif novo_status_pagamento == 'pendente':
                    pedido.status_entrega = 'aguardando'
                    pedido.status = 'pendente'
                elif novo_status_pagamento == 'rejeitado':
                    pedido.status_entrega = 'cancelado'
                    pedido.status = 'cancelado'

                pedido.save()

        return True

    except Exception as e:
        print(f"Erro ao atualizar status do pedido {pedido.id}: {e}")
        return False

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
# vendas/views/views.py

def estoque(request):
    """View para gerenciamento de estoque com filtros"""
    
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('login')

    # Obter parâmetros de filtro
    status_filter = request.GET.get('status', '')
    categoria_filter = request.GET.get('categoria', '')
    estoque_baixo_filter = request.GET.get('estoque_baixo', '')

    # Query base
    produtos = Produto.objects.prefetch_related('variacoes').all()
    
    # 🔥 APLICAR FILTROS
    # 1. Filtro por Status
    if status_filter == 'ativo':
        produtos = produtos.filter(ativo=True)
    elif status_filter == 'inativo':
        produtos = produtos.filter(ativo=False)
    
    # 2. Filtro por Categoria
    if categoria_filter:
        produtos = produtos.filter(categoria=categoria_filter)
    
    # 3. Filtro por Estoque Baixo
    if estoque_baixo_filter == 'sim':
        # Produtos com variações com estoque <= 5
        produtos_ids = []
        for p in produtos:
            if p.variacoes.filter(quantidade_estoque__lte=5).exists():
                produtos_ids.append(p.id)
        produtos = produtos.filter(id__in=produtos_ids)
    elif estoque_baixo_filter == 'nao':
        produtos_ids = []
        for p in produtos:
            if not p.variacoes.filter(quantidade_estoque__lte=5).exists():
                produtos_ids.append(p.id)
        produtos = produtos.filter(id__in=produtos_ids)

    produtos_com_precos = []
    total_estoque_geral = 0

    for p in produtos:
        variacao = p.variacoes.first()

        imagem_url = None
        preco = 0
        estoque = 0
        cor = 'N/A'
        tamanho = 'N/A'

        if variacao:
            preco = variacao.preco
            estoque = variacao.quantidade_estoque
            total_estoque_geral += estoque
            cor = variacao.cor
            tamanho = variacao.tamanho

            try:
                if variacao.imagem:
                    imagem_url = variacao.imagem.url.replace("http://", "https://")
            except Exception as e:
                print("ERRO IMAGEM:", e)

        if not imagem_url and p.imagem:
            try:
                imagem_url = p.imagem.url.replace("http://", "https://")
            except Exception as e:
                print("ERRO IMAGEM PRODUTO:", e)

        if not imagem_url:
            imagem_url = "https://placehold.co/300x200?text=Sem+Imagem"

        produtos_com_precos.append({
            'id': p.id,
            'nome': p.nome,
            'preco': float(preco),
            'quantidade_estoque': estoque,
            'cor': cor,
            'tamanho': tamanho,
            'imagem': imagem_url,
            'categoria': p.get_categoria_display(),
            'ativo': p.ativo,
            'data_cadastro': p.data_cadastro,
        })

    context = {
        'produtos': produtos_com_precos,
        'total_produtos': Produto.objects.count(),
        'produtos_ativos': Produto.objects.filter(ativo=True).count(),
        'produtos_inativos': Produto.objects.filter(ativo=False).count(),
        'total_estoque': total_estoque_geral,
    }

    return render(request, 'vendas/estoque.html', context)

@superuser_required
@login_required
@user_passes_test(lambda u: u.is_superuser)
def editar_produto(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)
    
    if request.method == 'POST':
        # Atualizar dados do produto base
        produto.nome = request.POST.get('nome')
        produto.descricao = request.POST.get('descricao')
        produto.categoria = request.POST.get('categoria')
        
        # 🔥 CORRIGIR AQUI - Status
        ativo = request.POST.get('ativo')
        if ativo == '1' or ativo == 'on' or ativo == 'true':
            produto.ativo = True
        else:
            produto.ativo = False
        
        # Atualizar imagem do produto se enviada
        if request.FILES.get('imagem'):
            produto.imagem = request.FILES['imagem']
        
        produto.save()
        
        # Atualizar a primeira variação
        variacao = produto.variacoes.first()
        if variacao:
            variacao.preco = request.POST.get('preco')
            variacao.quantidade_estoque = request.POST.get('quantidade_estoque')
            variacao.cor = request.POST.get('cor')
            variacao.tamanho = request.POST.get('tamanho')
            
            if request.FILES.get('imagem_variacao'):
                variacao.imagem = request.FILES['imagem_variacao']
            
            variacao.save()
        
        messages.success(request, 'Produto atualizado com sucesso!')
        return redirect('estoque')
    
    variacao = produto.variacoes.first()
    
    context = {
        'produto': produto,
        'variacao': variacao,
    }
    return render(request, 'vendas/editar_produto.html', context)
    
@superuser_required
@login_required
@user_passes_test(lambda u: u.is_superuser)
def deletar_produto(request, produto_id):
    """Exclui um produto"""
    produto = get_object_or_404(Produto, id=produto_id)
    nome = produto.nome
    produto.delete()
    messages.success(request, f'Produto "{nome}" excluído com sucesso!')
    return redirect('estoque')

@superuser_required
@login_required



def cadastrar_produto(request):
    if request.method == 'POST':
        # --- VALIDAÇÃO BÁSICA ---
        nome = request.POST.get('nome', '').strip()
        if not nome:
            messages.error(request, 'O nome do produto é obrigatório.')
            return render(request, 'vendas/cadastrar_produto.html')
        
        # --- 1. CRIAR O PRODUTO BASE ---
        produto = Produto.objects.create(
            nome=nome,
            descricao=request.POST.get('descricao', ''),
            categoria=request.POST.get('categoria', 'outros'),
            ativo=True
        )
        
        # --- 2. PROCESSAR AS VARIAÇÕES ---
        cores = request.POST.getlist('cor[]')
        tamanhos = request.POST.getlist('tamanho[]')
        precos = request.POST.getlist('preco[]')
        estoques = request.POST.getlist('quantidade_estoque[]')
        imagens = request.FILES.getlist('imagem_variacao[]')
        
        # Remove valores vazios
        variacoes_criadas = 0
        for i in range(len(cores)):
            preco_str = precos[i] if i < len(precos) else ''
            if not preco_str:
                continue  # Pula se não tiver preço
                
            try:
                preco = Decimal(preco_str)
                if preco <= 0:
                    continue
                    
                ProdutoVariacao.objects.create(
                    produto=produto,
                    cor=cores[i] if i < len(cores) else 'Branco',
                    tamanho=tamanhos[i] if i < len(tamanhos) else 'M',
                    preco=preco,
                    quantidade_estoque=int(estoques[i]) if i < len(estoques) and estoques[i] else 0,
                    imagem=imagens[i] if i < len(imagens) and imagens[i] else None
                )
                variacoes_criadas += 1
            except (ValueError, TypeError, Decimal.InvalidOperation):
                continue  # Pula se houver erro nos dados
        
        if variacoes_criadas == 0:
            # Se nenhuma variação foi criada, exclui o produto e avisa
            produto.delete()
            messages.error(request, 'É necessário cadastrar pelo menos uma variação válida (com preço).')
            return render(request, 'vendas/cadastrar_produto.html')
        
        messages.success(request, f'Produto "{produto.nome}" cadastrado com {variacoes_criadas} variações!')
        return redirect('estoque')
    
    return render(request, 'vendas/cadastrar_produto.html')

def meus_pedidos(request):
    pedidos = Pedido.objects.filter(usuario=request.user)\
        .prefetch_related('itens_pedido__produto')\
        .order_by('-data_criacao')

    return render(request, 'vendas/meus_pedidos.html', {
        'pedidos': pedidos
    })


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



def login_view(request):
    # 🔥 SE O USUÁRIO JÁ ESTIVER LOGADO, REDIRECIONA
    if request.user.is_authenticated:
        return redirect('pagina_inicial')
    
    # 🔥 PEGA O CARRINHO DA SESSÃO
    carrinho_salvo = request.session.get('carrinho', {})
    
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        # ==========================================================
        # LOGIN
        # ==========================================================
        if form_type == 'login':
            username = request.POST.get('username')
            password = request.POST.get('password')
            
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                carrinho_antigo = request.session.get('carrinho', {})
                login(request, user)
                
                if carrinho_antigo:
                    for chave, item in carrinho_antigo.items():
                        try:
                            variacao_id = item.get('variacao_id')
                            if variacao_id:
                                variacao = ProdutoVariacao.objects.get(id=variacao_id)
                                CarrinhoItem.objects.get_or_create(
                                    usuario=user,
                                    variacao=variacao,
                                    defaults={'quantidade': item.get('quantidade', 1)}
                                )
                        except Exception as e:
                            print(f"Erro ao restaurar item: {e}")
                    
                    if 'carrinho' in request.session:
                        del request.session['carrinho']
                
                messages.success(request, f'Bem-vindo(a) {user.first_name or user.username}!')
                
                next_url = request.GET.get('next', 'pagina_inicial')
                if 'carrinho' in next_url:
                    return redirect('visualizar_carrinho')
                return redirect(next_url)
            else:
                messages.error(request, 'Usuário ou senha inválidos.')
        
        # ==========================================================
        # CADASTRO (CRIAR CONTA)
        # ==========================================================
        elif form_type == 'cadastro':
            email = request.POST.get('email', '').strip()
            
            if not email:
                messages.error(request, 'E-mail é obrigatório para cadastro.')
                return render(request, 'vendas/login.html')
            
            # 🔥 SALVA O EMAIL NA SESSÃO
            request.session['email_cadastro'] = email
            
            # 🔥 SALVA O CARRINHO EM UMA CHAVE PERSISTENTE
            if carrinho_salvo:
                request.session['carrinho_persistente'] = carrinho_salvo
                request.session.modified = True
                request.session.save()
                print(f"💾 CARRINHO SALVO EM 'carrinho_persistente': {carrinho_salvo}")
            else:
                print("⚠️ Nenhum carrinho para salvar")
            
            messages.info(request, 'Preencha seus dados para finalizar o cadastro.')
            return redirect('registrar_com_endereco')
    
    return render(request, 'vendas/login.html')


# vendas/views/views.py


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
