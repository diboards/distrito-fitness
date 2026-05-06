from django import forms
from .models import Venda, Produto
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import EnderecoEntrega
from .models import Perfil, Endereco


class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ['nome', 'descricao', 'preco', 'quantidade_estoque', 'cor', 'tamanho', 'categoria', 'imagem']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Digite o nome do produto'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Digite a descrição do produto'
            }),
            'preco': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            }),
            'quantidade_estoque': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0'
            }),
            'cor': forms.Select(attrs={
                'class': 'form-control'
            }),
            'tamanho': forms.Select(attrs={
                'class': 'form-control'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-control'
            }),
            'imagem': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
        labels = {
            'nome': 'Nome do Produto',
            'descricao': 'Descrição',
            'preco': 'Preço (R$)',
            'quantidade_estoque': 'Quantidade em Estoque',
            'cor': 'Cor',
            'tamanho': 'Tamanho',
            'categoria': 'Categoria',
            'imagem': 'Imagem do Produto'
        }
    
    def clean_preco(self):
        preco = self.cleaned_data.get('preco')
        if preco <= 0:
            raise forms.ValidationError("O preço deve ser maior que zero.")
        return preco
    
    def clean_quantidade_estoque(self):
        quantidade = self.cleaned_data.get('quantidade_estoque')
        if quantidade < 0:
            raise forms.ValidationError("A quantidade em estoque não pode ser negativa.")
        return quantidade
    
    def clean_imagem(self):
        imagem = self.cleaned_data.get('imagem')

        # Se não enviou nova imagem → mantém a atual
        if not imagem:
            return imagem

        # 🔥 Se for upload novo (arquivo mesmo)
        if hasattr(imagem, 'size'):
            if imagem.size > 2 * 1024 * 1024:
                raise forms.ValidationError("Imagem muito grande (máx 2MB).")

        # 🔥 Se for Cloudinary (edição de produto)
        elif hasattr(imagem, 'public_id'):
            # objeto do Cloudinary → NÃO tem size
            return imagem

        return imagem   

class VendaForm(forms.ModelForm):
    class Meta:
        model = Venda
        fields = ['produto', 'quantidade', 'observacoes', 'status']
        widgets = {
            'produto': forms.Select(attrs={'class': 'form-control'}),
            'quantidade': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Quantidade'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações adicionais'
            }),
            'status': forms.Select(attrs={'class': 'form-control'})
        }

# forms.py - mantenha apenas este
class UsuarioComEnderecoForm(forms.Form):
    # Dados do usuário
    nome = forms.CharField(max_length=100, required=True, label='Nome Completo')
    email = forms.EmailField(required=True, label='E-mail')
    cpf = forms.CharField(max_length=14, required=True, label='CPF')
    celular = forms.CharField(max_length=15, required=True, label='Celular')
    password1 = forms.CharField(
        widget=forms.PasswordInput,
        min_length=6,
        required=True,
        label='Senha'
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput,
        min_length=6,
        required=True,
        label='Confirmar Senha'
    )
    
    # Dados do endereço
    cep = forms.CharField(max_length=9, required=True, label='CEP')
    rua = forms.CharField(max_length=100, required=True, label='Rua')
    numero = forms.CharField(max_length=10, required=True, label='Número')
    complemento = forms.CharField(max_length=50, required=False, label='Complemento')
    bairro = forms.CharField(max_length=50, required=True, label='Bairro')
    cidade = forms.CharField(max_length=50, required=True, label='Cidade')
    estado = forms.CharField(max_length=2, required=True, label='Estado')
    principal = forms.BooleanField(required=False, initial=True, label='Endereço principal')
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('As senhas não coincidem')
        
        return cleaned_data  
        
class OrcamentoForm(forms.Form):
    AMBIENTE_CHOICES = [
        ('', 'Escolha uma opção'),
        ('sala', 'Sala de Estar'),
        ('quarto', 'Quarto'),
        ('cozinha', 'Cozinha'),
        ('banheiro', 'Banheiro'),
        ('escritorio', 'Escritório'),
        ('outro', 'Outro'),
    ]
    ORCAMENTO_CHOICES = [
        ('', 'Escolha uma opção'),
        ('5-10', 'R$ 5.000 - R$ 10.000'),
        ('10-20', 'R$ 10.000 - R$ 20.000'),
        ('20-50', 'R$ 20.000 - R$ 50.000'),
        ('50+', 'Acima de R$ 50.000'),
    ]

    nome = forms.CharField(
        label='Seu nome',
        required=True,
        error_messages={'required': 'Insira seu nome.'}
    )
    telefone = forms.CharField(
        label='DDD + Whatsapp',
        max_length=15,
        required=True,
        error_messages={'required': 'Insira o número de WhatsApp.'}
    )
    ambiente = forms.ChoiceField(
        choices=AMBIENTE_CHOICES,
        required=True,
        error_messages={'required': 'Escolha um ambiente.'}
    )
    orcamento = forms.ChoiceField(
        choices=ORCAMENTO_CHOICES,
        required=True,
        error_messages={'required': 'Escolha um orçamento.'}
    )

    def clean_ambiente(self):
        data = self.cleaned_data.get('ambiente')
        if data == '':
            raise forms.ValidationError('Escolha um ambiente.')
        return data

    def clean_orcamento(self):
        data = self.cleaned_data.get('orcamento')
        if data == '':
            raise forms.ValidationError('Escolha um orçamento.')
        return data

class PerfilForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False, label="Nome")
    last_name = forms.CharField(max_length=30, required=False, label="Sobrenome")
    email = forms.EmailField(required=True, label="E-mail")
    
    class Meta:
        model = Perfil
        fields = ['telefone', 'cpf', 'data_nascimento', 'avatar', 'bio']
        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 00000-0000'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Conte um pouco sobre você...'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.usuario:
            self.fields['first_name'].initial = self.instance.usuario.first_name
            self.fields['last_name'].initial = self.instance.usuario.last_name
            self.fields['email'].initial = self.instance.usuario.email
    
    def save(self, commit=True):
        perfil = super().save(commit=False)
        if commit:
            perfil.save()
            # Atualiza dados do User
            usuario = perfil.usuario
            usuario.first_name = self.cleaned_data['first_name']
            usuario.last_name = self.cleaned_data['last_name']
            usuario.email = self.cleaned_data['email']
            usuario.save()
        return perfil

