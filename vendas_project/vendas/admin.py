# Register your models here.
from django.contrib import admin
from .models import Produto, Venda



@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'preco', 'quantidade_estoque', 'cor', 'tamanho', 'ativo']
    list_filter = ['cor', 'tamanho', 'ativo', 'data_cadastro']
    search_fields = ['nome', 'descricao']
    readonly_fields = ['data_cadastro']

@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ['id', 'produto', 'quantidade', 'total', 'data_venda', 'status']
    list_filter = ['status', 'data_venda']
    readonly_fields = ['data_venda', 'total']