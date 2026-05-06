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
def adicionar_endereco(request):
    """Adiciona um novo endereço via AJAX ou POST normal"""
    try:
        form = EnderecoEntregaForm(request.POST)
        
        if form.is_valid():
            endereco = form.save(commit=False)
            endereco.usuario = request.user
            
            # Se for o primeiro endereço ou marcado como principal
            if endereco.principal or not EnderecoEntrega.objects.filter(usuario=request.user).exists():
                # Remove principal de outros endereços
                EnderecoEntrega.objects.filter(usuario=request.user).update(principal=False)
                endereco.principal = True
            
            endereco.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'endereco': {
                        'id': endereco.id,
                        'rua': endereco.rua,
                        'numero': endereco.numero,
                        'bairro': endereco.bairro,
                        'cidade': endereco.cidade,
                        'estado': endereco.estado,
                        'cep': endereco.cep,
                        'principal': endereco.principal
                    },
                    'message': 'Endereço adicionado com sucesso!'
                })
            
            messages.success(request, 'Endereço adicionado com sucesso!')
            return redirect('meus_enderecos')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                }, status=400)
            
            messages.error(request, 'Erro ao adicionar endereço. Verifique os campos.')
            return redirect('meus_enderecos')
            
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
        
        messages.error(request, f'Erro ao adicionar endereço: {str(e)}')
        return redirect('meus_enderecos')

# vendas/views/enderecos.py

@login_required
def editar_endereco(request, endereco_id):
    """Edita um endereço existente via AJAX"""
    endereco = get_object_or_404(Endereco, id=endereco_id, usuario=request.user)
    
    if request.method == 'POST':
        form = EnderecoForm(request.POST, instance=endereco)
        if form.is_valid():
            endereco_atualizado = form.save(commit=False)
            
            # Se marcou como principal, remove principal dos outros
            if endereco_atualizado.principal:
                Endereco.objects.filter(usuario=request.user).exclude(id=endereco_id).update(principal=False)
            
            endereco_atualizado.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Endereço atualizado com sucesso!'})
            else:
                messages.success(request, 'Endereço atualizado com sucesso!')
                return redirect('meus_enderecos')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Erro ao atualizar endereço. Verifique os campos.'})
            else:
                messages.error(request, 'Erro ao atualizar endereço.')
    else:
        form = EnderecoForm(instance=endereco)
    
    return render(request, 'vendas/editar_endereco.html', {'form': form, 'endereco': endereco})

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
