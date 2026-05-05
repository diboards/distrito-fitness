from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Perfil, Endereco
from .forms import PerfilForm, EnderecoForm

@login_required
def meu_perfil(request):
    perfil, created = Perfil.objects.get_or_create(usuario=request.user)
    
    if request.method == 'POST':
        form = PerfilForm(request.POST, request.FILES, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('meu_perfil')
    else:
        form = PerfilForm(instance=perfil)
    
    context = {
        'form': form,
        'perfil': perfil,
    }
    return render(request, 'vendas/meu_perfil.html', context)

@login_required
def meus_enderecos(request):
    enderecos = Endereco.objects.filter(usuario=request.user)
    
    if request.method == 'POST':
        form = EnderecoForm(request.POST)
        if form.is_valid():
            endereco = form.save(commit=False)
            endereco.usuario = request.user
            
            # Se este for o primeiro endereço ou marcado como principal
            if endereco.is_principal or not enderecos.exists():
                endereco.is_principal = True
                # Remove principal de outros endereços
                Endereco.objects.filter(usuario=request.user).update(is_principal=False)
            
            endereco.save()
            messages.success(request, 'Endereço adicionado com sucesso!')
            return redirect('meus_enderecos')
    else:
        form = EnderecoForm()
    
    context = {
        'enderecos': enderecos,
        'form': form,
    }
    return render(request, 'vendas/meus_enderecos.html', context)

@login_required
def editar_endereco(request, endereco_id):
    endereco = get_object_or_404(Endereco, id=endereco_id, usuario=request.user)
    
    if request.method == 'POST':
        form = EnderecoForm(request.POST, instance=endereco)
        if form.is_valid():
            endereco_atualizado = form.save(commit=False)
            
            if endereco_atualizado.is_principal:
                Endereco.objects.filter(usuario=request.user).exclude(id=endereco_id).update(is_principal=False)
            
            endereco_atualizado.save()
            messages.success(request, 'Endereço atualizado com sucesso!')
            return redirect('meus_enderecos')
    else:
        form = EnderecoForm(instance=endereco)
    
    return render(request, 'vendas/editar_endereco.html', {'form': form, 'endereco': endereco})

@login_required
def deletar_endereco(request, endereco_id):
    endereco = get_object_or_404(Endereco, id=endereco_id, usuario=request.user)
    
    if request.method == 'POST':
        endereco.delete()
        messages.success(request, 'Endereço removido com sucesso!')
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False}, status=400)

@login_required
def definir_endereco_principal(request, endereco_id):
    endereco = get_object_or_404(Endereco, id=endereco_id, usuario=request.user)
    
    # Remove principal de todos os endereços
    Endereco.objects.filter(usuario=request.user).update(is_principal=False)
    
    # Define o novo endereço como principal
    endereco.is_principal = True
    endereco.save()
    
    messages.success(request, 'Endereço principal definido com sucesso!')
    return redirect('meus_enderecos')
