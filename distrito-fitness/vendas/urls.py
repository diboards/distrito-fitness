from django.urls import path
from django.http import HttpResponse

def home(request):
    return HttpResponse("Página inicial funcionando!")

def estoque(request):
    return HttpResponse("Página de estoque!")

urlpatterns = [
    path('', home, name='home'),
    path('estoque/', estoque, name='estoque'),
]
