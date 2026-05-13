# vendas/views_enderecos.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User

from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import EnderecoEntrega, CarrinhoItem
from .forms import EnderecoEntregaForm
from django.db import IntegrityError


@login_required
def meus_enderecos(request):
    """Página principal de gerenciamento de endereços"""
    enderecos = EnderecoEntrega.objects.filter(usuario=request.user).order_by('-principal', '-id')
    
    context = {
        'enderecos': enderecos,
        'total_enderecos': enderecos.count(),
    }
    return render(request, 'vendas/meus_enderecos.html', context)

# vendas/views_enderecos.py

@login_required
@require_http_methods(["POST"])
def adicionar_ou_editar_endereco(request):
    """Adiciona ou edita um endereço via AJAX"""
    try:
        endereco_id = request.POST.get('endereco_id')
        
        # Validação dos campos obrigatórios
        rua = request.POST.get('rua')
        numero = request.POST.get('numero')
        bairro = request.POST.get('bairro')
        cidade = request.POST.get('cidade')
        estado = request.POST.get('estado')
        cep = request.POST.get('cep')
        
        # Log para debug
        print(f"DEBUG - endereco_id: {endereco_id}")
        print(f"DEBUG - Dados recebidos: rua={rua}, numero={numero}, bairro={bairro}, cidade={cidade}, estado={estado}, cep={cep}")
        
        if not all([rua, numero, bairro, cidade, estado, cep]):
            return JsonResponse({
                'success': False,
                'error': 'Todos os campos obrigatórios devem ser preenchidos.'
            })
        
        principal = request.POST.get('principal') == 'on'
        complemento = request.POST.get('complemento', '')
        
        if endereco_id and endereco_id != '':
            # ===== MODO EDITAR =====
            endereco = get_object_or_404(EnderecoEntrega, id=endereco_id, usuario=request.user)
            
            # Atualiza os campos
            endereco.rua = rua
            endereco.numero = numero
            endereco.complemento = complemento
            endereco.bairro = bairro
            endereco.cidade = cidade
            endereco.estado = estado
            endereco.cep = cep
            
            if principal:
                # Remove principal de outros endereços
                EnderecoEntrega.objects.filter(usuario=request.user, principal=True).update(principal=False)
                endereco.principal = True
            else:
                endereco.principal = False
            
            endereco.save()
            message = 'Endereço atualizado com sucesso!'
            print(f"DEBUG - Endereço {endereco_id} atualizado com sucesso")
            
        else:
            # ===== MODO ADICIONAR =====
            if principal:
                EnderecoEntrega.objects.filter(usuario=request.user, principal=True).update(principal=False)
            
            endereco = EnderecoEntrega(
                usuario=request.user,
                cep=cep,
                rua=rua,
                numero=numero,
                complemento=complemento,
                bairro=bairro,
                cidade=cidade,
                estado=estado,
                principal=principal if principal else not EnderecoEntrega.objects.filter(usuario=request.user).exists()
            )
            endereco.save()
            message = 'Endereço adicionado com sucesso!'
            print(f"DEBUG - Novo endereço criado com ID {endereco.id}")
        
        return JsonResponse({
            'success': True,
            'message': message,
            'endereco_id': endereco.id
        })
        
    except Exception as e:
        print(f"DEBUG - Erro: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
def deletar_endereco(request, endereco_id):
    """Remove um endereço"""
    endereco = get_object_or_404(EnderecoEntrega, id=endereco_id, usuario=request.user)
    
    # Se for o endereço principal, não pode deletar
    if endereco.principal:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'Não é possível excluir o endereço principal. Defina outro como principal primeiro.'
            }, status=400)
        
        messages.error(request, 'Não é possível excluir o endereço principal. Defina outro como principal primeiro.')
        return redirect('meus_enderecos')
    
    endereco.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Endereço excluído com sucesso!'
        })
    
    messages.success(request, 'Endereço excluído com sucesso!')
    return redirect('meus_enderecos')



@login_required
@require_http_methods(["POST"])
def definir_principal(request, endereco_id):
    """Define um endereço como principal"""
    try:
        # Busca o endereço que será o principal
        endereco = get_object_or_404(EnderecoEntrega, id=endereco_id, usuario=request.user)
        
        print(f"DEBUG - Usuário: {request.user.username}")
        print(f"DEBUG - Endereço ID {endereco_id} - Antes: principal={endereco.principal}")
        
        # Método 1: Usando update direto no banco
        # Remove principal de TODOS os endereços deste usuário
        atualizados = EnderecoEntrega.objects.filter(usuario=request.user).update(principal=False)
        print(f"DEBUG - {atualizados} endereços tiveram principal removido")
        
        # Define o novo endereço como principal
        endereco.principal = True
        endereco.save(update_fields=['principal'])
        
        # Verifica se salvou corretamente
        verificado = EnderecoEntrega.objects.get(id=endereco_id)
        print(f"DEBUG - Depois: Endereço {endereco_id} principal={verificado.principal}")
        
        # Retorna sucesso
        return JsonResponse({
            'success': True,
            'message': 'Endereço principal definido com sucesso!',
            'endereco_id': endereco.id
        })
        
    except Exception as e:
        print(f"DEBUG - Erro: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
        
@login_required
def listar_enderecos_api(request):
    """API para listar endereços (usado no checkout)"""
    enderecos = EnderecoEntrega.objects.filter(usuario=request.user).order_by('-principal', '-id')
    
    enderecos_data = [{
        'id': e.id,
        'rua': e.rua,
        'numero': e.numero,
        'complemento': e.complemento,
        'bairro': e.bairro,
        'cidade': e.cidade,
        'estado': e.estado,
        'cep': e.cep,
        'principal': e.principal,
        'endereco_completo': f"{e.rua}, {e.numero} - {e.bairro}, {e.cidade}/{e.estado}"
    } for e in enderecos]
    
    return JsonResponse({
        'success': True,
        'enderecos': enderecos_data,
        'total': enderecos.count()
    })

# vendas/views/enderecos.py

@login_required
def adicionar_endereco_checkout(request):
    """View para adicionar endereço (AJAX)"""
    if request.method == 'POST':
        try:
            # Verifica se é para adicionar ou editar
            endereco_id = request.POST.get('endereco_id')
            
            if endereco_id:
                # ===== MODO EDITAR =====
                endereco = get_object_or_404(Endereco, id=endereco_id, usuario=request.user)
                
                endereco.rua = request.POST.get('rua')
                endereco.numero = request.POST.get('numero')
                endereco.complemento = request.POST.get('complemento', '')
                endereco.bairro = request.POST.get('bairro')
                endereco.cidade = request.POST.get('cidade')
                endereco.estado = request.POST.get('estado')
                endereco.cep = request.POST.get('cep')
                
                principal = request.POST.get('principal') == 'on'
                
                if principal:
                    # Remove principal de outros endereços
                    Endereco.objects.filter(usuario=request.user, principal=True).update(principal=False)
                    endereco.principal = True
                else:
                    endereco.principal = False
                
                endereco.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Endereço atualizado com sucesso!'
                })
                
            else:
                # ===== MODO ADICIONAR =====
                principal = request.POST.get('principal') == 'on'
                
                # Se for principal, remove principal de outros
                if principal:
                    Endereco.objects.filter(usuario=request.user, principal=True).update(principal=False)
                
                endereco = Endereco(
                    usuario=request.user,
                    cep=request.POST.get('cep'),
                    rua=request.POST.get('rua'),
                    numero=request.POST.get('numero'),
                    complemento=request.POST.get('complemento', ''),
                    bairro=request.POST.get('bairro'),
                    cidade=request.POST.get('cidade'),
                    estado=request.POST.get('estado'),
                    principal=principal
                )
                endereco.save()
                
                return JsonResponse({
                    'success': True,
                    'endereco_id': endereco.id,
                    'message': 'Endereço adicionado com sucesso!'
                })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método não permitido'})



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
            
            # ===== 1. SALVAR O CARRINHO DA SESSÃO ANTES DE CRIAR O USUÁRIO =====
            carrinho_sessao = request.session.get('carrinho', {})
            print("DEBUG - Carrinho na sessão:", carrinho_sessao)
            
            # ===== 2. CRIA O USUÁRIO =====
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

            # ===== 3. TRANSFERIR O CARRINHO DA SESSÃO PARA O USUÁRIO (CORRIGIDO - SEM DUPLICIDADE) =====
            if carrinho_sessao:
                from .models import Produto  # Importar aqui para evitar circular
                
                # Dicionário para agrupar itens duplicados
                itens_agrupados = {}
                
                for chave, dados in carrinho_sessao.items():
                    produto_id = dados.get('id')
                    cor = dados.get('cor', '')
                    tamanho = dados.get('tamanho', '')
                    quantidade = dados.get('quantidade', 1)
                    
                    if not produto_id:
                        # Tenta extrair da chave como fallback
                        try:
                            produto_id = int(chave.split('_')[0]) if chave.split('_')[0].isdigit() else None
                        except:
                            produto_id = None
                    
                    if produto_id:
                        # Chave única para agrupar (produto + cor + tamanho)
                        grupo_key = f"{produto_id}_{cor}_{tamanho}"
                        
                        if grupo_key in itens_agrupados:
                            itens_agrupados[grupo_key]['quantidade'] += quantidade
                        else:
                            itens_agrupados[grupo_key] = {
                                'produto_id': produto_id,
                                'cor': cor,
                                'tamanho': tamanho,
                                'quantidade': quantidade
                            }
                
                # Agora transfere os itens agrupados (sem duplicidade)
                for grupo_key, dados in itens_agrupados.items():
                    try:
                        produto = Produto.objects.get(id=dados['produto_id'])
                        
                        # Verifica se já existe no carrinho do usuário
                        item, created = CarrinhoItem.objects.get_or_create(
                            usuario=user,
                            produto=produto,
                            cor_selecionada=dados.get('cor', ''),
                            tamanho_selecionado=dados.get('tamanho', ''),
                            defaults={'quantidade': dados.get('quantidade', 1)}
                        )
                        if not created:
                            item.quantidade += dados.get('quantidade', 1)
                            item.save()
                        
                        print(f"DEBUG - Produto {produto.nome} (cor: {dados.get('cor', '')}, tam: {dados.get('tamanho', '')}) - quantidade: {item.quantidade}")
                        
                    except Produto.DoesNotExist:
                        print(f"DEBUG - Produto não encontrado: {dados['produto_id']}")
                    except Exception as e:
                        print(f"DEBUG - Erro ao processar produto: {str(e)}")
                
                # Limpa o carrinho da sessão
                request.session['carrinho'] = {}
                request.session.modified = True
            
            # Faz login automático
            user = authenticate(username=email, password=password1)
            if user:
                login(request, user)
                # Limpa a session
                if 'email_cadastro' in request.session:
                    del request.session['email_cadastro']
                
                messages.success(request, 'Conta criada com sucesso!')

                # Verifica se o carrinho foi transferido
                itens_carrinho = CarrinhoItem.objects.filter(usuario=user)
                print(f"DEBUG - Itens no carrinho após transferência: {itens_carrinho.count()}")
                
                return redirect('visualizar_carrinho')
                
        except IntegrityError:
            messages.error(request, 'Este e-mail já está cadastrado')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Erro ao criar conta: {str(e)}')
    
    return render(request, 'vendas/registrar_com_endereco.html', {
        'email': email
    })
