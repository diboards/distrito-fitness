from django import forms
from .models import Venda, Produto
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import EnderecoEntrega

from .models import Produto, ProdutoVariacao, Venda, EnderecoEntrega, Perfil


# vendas/forms.py - Substitua a classe ProdutoForm por esta:

# vendas/forms.py - Substitua a classe ProdutoForm

class ProdutoForm(forms.ModelForm):
    """Formulário para o produto base (sem preço, cor, tamanho, estoque)"""
    class Meta:
        model = Produto
        fields = ['nome', 'descricao', 'categoria', 'imagem', 'ativo']
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
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'imagem': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'nome': 'Nome do Produto',
            'descricao': 'Descrição',
            'categoria': 'Categoria',
            'imagem': 'Imagem do Produto',
            'ativo': 'Produto Ativo',
        }
    
    def clean_imagem(self):
        imagem = self.cleaned_data.get('imagem')
        if not imagem:
            return imagem
        if hasattr(imagem, 'size') and imagem.size > 2 * 1024 * 1024:
            raise forms.ValidationError("Imagem muito grande (máx 2MB).")
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

# Forms Meu perfil
class Perfil(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    telefone = models.CharField(
        max_length=15, 
        blank=True, 
        null=True,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Número de telefone inválido")]
    )
    cpf = models.CharField(max_length=14, blank=True, null=True, verbose_name="CPF")
    data_nascimento = models.DateField(blank=True, null=True)
    #avatar = models.ImageField(upload_to='avatars/', blank=True, null=True) foto de perfil
    bio = models.TextField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfis"

    def __str__(self):
        return f"Perfil de {self.usuario.username}"


# Forms de Endereço
class EnderecoEntregaForm(forms.ModelForm):
    class Meta:
        model = EnderecoEntrega
        fields = ['rua', 'numero', 'complemento', 'bairro', 'cidade', 'estado', 'cep', 'principal']
        widgets = {
            'rua': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Rua, Avenida...'}),
            'numero': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número'}),
            'complemento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apto, Bloco...'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bairro'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cidade'}),
            'estado': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('', 'Selecione...'),
                ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'),
                ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'),
                ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'),
                ('MG', 'Minas Gerais'), ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'),
                ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
                ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'),
                ('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantins')
            ]),
            'cep': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000-000'}),
            'principal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
