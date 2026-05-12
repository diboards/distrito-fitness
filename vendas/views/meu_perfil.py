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
        form = PerfilForm(request.POST, instance=perfil)
        if form.is_valid():
            form.save()  # O save do form já atualiza User e Perfil
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('meu_perfil')
        else:
            messages.error(request, 'Erro ao atualizar perfil. Verifique os campos.')
    else:
        # Inicializa o form com os dados atuais
        initial_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        }
        form = PerfilForm(instance=perfil, initial=initial_data)
    
    context = {
        'form': form,
        'perfil': perfil,
    }
    return render(request, 'vendas/meu_perfil.html', context)


