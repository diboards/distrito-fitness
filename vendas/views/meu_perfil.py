from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse

from vendas.forms import PerfilForm
from vendas.models import Perfil  # ou from ..models import Perfil

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


