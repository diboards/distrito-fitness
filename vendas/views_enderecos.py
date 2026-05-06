# vendas/views_enderecos.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import EnderecoEntrega
from .forms import EnderecoEntregaForm


@login_required
def meus_enderecos(request):
    """Página principal de gerenciamento de endereços"""
    enderecos = EnderecoEntrega.objects.filter(usuario=request.user).order_by('-principal', '-id')
    
    context = {
        'enderecos': enderecos,
        'total_enderecos': enderecos.count(),
    }
    return render(request, 'vendas/meus_enderecos.html', context)

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
        
        if not all([rua, numero, bairro, cidade, estado, cep]):
            return JsonResponse({
                'success': False,
                'error': 'Todos os campos obrigatórios devem ser preenchidos.'
            })
        
        principal = request.POST.get('principal') == 'on'
        
        if endereco_id and endereco_id != '':
            # ===== MODO EDITAR =====
            endereco = get_object_or_404(EnderecoEntrega, id=endereco_id, usuario=request.user)
            
            endereco.rua = rua
            endereco.numero = numero
            endereco.complemento = request.POST.get('complemento', '')
            endereco.bairro = bairro
            endereco.cidade = cidade
            endereco.estado = estado
            endereco.cep = cep
            
            if principal:
                EnderecoEntrega.objects.filter(usuario=request.user, principal=True).update(principal=False)
                endereco.principal = True
            else:
                endereco.principal = False
            
            endereco.save()
            message = 'Endereço atualizado com sucesso!'
            
        else:
            # ===== MODO ADICIONAR =====
            if principal:
                EnderecoEntrega.objects.filter(usuario=request.user, principal=True).update(principal=False)
            
            endereco = EnderecoEntrega(
                usuario=request.user,
                cep=cep,
                rua=rua,
                numero=numero,
                complemento=request.POST.get('complemento', ''),
                bairro=bairro,
                cidade=cidade,
                estado=estado,
                principal=principal if principal else not EnderecoEntrega.objects.filter(usuario=request.user).exists()
            )
            endereco.save()
            message = 'Endereço adicionado com sucesso!'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'endereco_id': endereco.id
        })
        
    except Exception as e:
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
    endereco = get_object_or_404(EnderecoEntrega, id=endereco_id, usuario=request.user)
    
    # Remove principal de todos os endereços
    EnderecoEntrega.objects.filter(usuario=request.user).update(principal=False)
    
    # Define o novo endereço como principal
    endereco.principal = True
    endereco.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Endereço principal definido com sucesso!',
            'endereco_id': endereco.id
        })
    
    messages.success(request, 'Endereço principal definido com sucesso!')
    return redirect('meus_enderecos')

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
