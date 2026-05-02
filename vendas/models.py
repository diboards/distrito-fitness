from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.contrib.auth.models import BaseUserManager
from decimal import Decimal
from cloudinary.models import CloudinaryField


class Produto(models.Model):
    CATEGORIA_CHOICES = [
        ('lancamentos', 'Lançamentos'),
        ('promocoes', 'Promoções'),
        ('conjuntos', 'Conjuntos'),
        ('outros', 'Outros'),
    ]

    TAMANHO_CHOICES = [
        ('PP', 'PP'),
        ('P', 'P'),
        ('M', 'M'),
        ('G', 'G'),
        ('GG', 'GG'),
        ('U', 'Único'),
    ]
    
    COR_CHOICES = [
        ('Vermelho', 'Vermelho'),
        ('Azul', 'Azul'),
        ('Verde', 'Verde'),
        ('Amarelo', 'Amarelo'),
        ('Preto', 'Preto'),
        ('Branco', 'Branco'),
        ('Rosa', 'Rosa'),
        ('Roxo', 'Roxo'),
        ('Laranja', 'Laranja'),
        ('Cinza', 'Cinza'),
        ('Marrom', 'Marrom'),
        ('Outro', 'Outro'),
    ]
    
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    quantidade_estoque = models.PositiveIntegerField(default=0)
    cor = models.CharField(max_length=20, choices=COR_CHOICES, default='Branco')
    tamanho = models.CharField(max_length=10, choices=TAMANHO_CHOICES, default='M')
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='outros')

    # ✅ CLOUDINARY
    imagem = CloudinaryField('imagem', blank=True, null=True)

    data_cadastro = models.DateTimeField(default=timezone.now)
    ativo = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.nome} ({self.cor}, {self.tamanho})"


class CarrinhoItem(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    produto = models.ForeignKey('Produto', on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField(default=1)
    cor_selecionada = models.CharField(max_length=50, blank=True, null=True)
    tamanho_selecionado = models.CharField(max_length=10, blank=True, null=True)

    # ⚠️ IMPORTANTE: também precisa ser Cloudinary
    imagem = CloudinaryField('imagem', blank=True, null=True)

    data_adicionado = models.DateTimeField(auto_now_add=True)
    
    @property
    def subtotal(self):
        return self.produto.preco * self.quantidade
    
    def __str__(self):
        return f"{self.produto.nome} - {self.usuario.username}"
        
class ItemPedido(models.Model):
    pedido = models.ForeignKey('Pedido', on_delete=models.CASCADE, related_name='itens_pedido')
    produto = models.ForeignKey('Produto', on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField(default=1)
    cor_selecionada = models.CharField(max_length=50, blank=True, null=True)
    tamanho_selecionado = models.CharField(max_length=10, blank=True, null=True)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
        
    @property
    def subtotal(self):
            return self.preco_unitario * self.quantidade
        
    def __str__(self):
            return f"{self.produto.nome} - Pedido #{self.pedido.id}"


class EnderecoEntrega(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="enderecos")
    cep = models.CharField(max_length=9)
    rua = models.CharField(max_length=100)
    numero = models.CharField(max_length=10)
    complemento = models.CharField(max_length=50, blank=True)
    bairro = models.CharField(max_length=50)
    cidade = models.CharField(max_length=50)
    estado = models.CharField(max_length=2)
    principal = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.rua}, {self.numero} - {self.bairro}, {self.cidade}/{self.estado}"
    class Meta:
        verbose_name_plural = "Endereços de Entrega"

class Pedido(models.Model):

    METODO_PAGAMENTO_CHOICES = [
        ('pix', 'PIX'),
        ('cartao', 'Cartão de Crédito'),
    ]

    TIPO_ENTREGA_CHOICES = [
        ('retirada', 'Retirada na Loja'),
        ('entrega', 'Entrega'),
    ]

    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aguardando_aprovacao', 'Aguardando Aprovação'),
        ('aprovado', 'Aprovado'),
        ('processando', 'Processando'),
        ('enviado', 'Enviado'),
        ('entregue', 'Entregue'),
        ('cancelado', 'Cancelado'),
    ]

    # 🔥 NOVOS (não quebram nada)
    STATUS_PAGAMENTO_CHOICES = [
        ('pendente', 'Pendente'),
        ('aprovado', 'Aprovado'),
        ('rejeitado', 'Rejeitado'),
    ]

    STATUS_ENTREGA_CHOICES = [
        ('aguardando', 'Aguardando'),
        ('preparando', 'Preparando'),
        ('enviado', 'Enviado'),
        ('entregue', 'Entregue'),
        ('retirado', 'Retirado'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    data_criacao = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')

    # ✅ NOVOS CAMPOS
    status_pagamento = models.CharField(
        max_length=20,
        choices=STATUS_PAGAMENTO_CHOICES,
        default='pendente'
    )

    status_entrega = models.CharField(
        max_length=20,
        choices=STATUS_ENTREGA_CHOICES,
        default='aguardando'
    )

    endereco_entrega = models.ForeignKey('EnderecoEntrega', on_delete=models.SET_NULL, null=True, blank=True)
    metodo_pagamento = models.CharField(max_length=20, choices=METODO_PAGAMENTO_CHOICES, default='pix')
    tipo_entrega = models.CharField(max_length=20, choices=TIPO_ENTREGA_CHOICES, default='retirada')
    frete = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    id_mercado_pago = models.CharField(max_length=100, blank=True, null=True)

    qr_code = models.TextField(blank=True, null=True)
    qr_code_base64 = models.TextField(blank=True, null=True)

    numero_cartao = models.CharField(max_length=4, blank=True, null=True)
    validade_cartao = models.CharField(max_length=5, blank=True, null=True)
    nome_cartao = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Pedido #{self.id} - {self.usuario.username}"

    class Meta:
        ordering = ['-data_criacao']

class EmailUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
            if not email:
                raise ValueError('O email é obrigatório')
            email = self.normalize_email(email)
            user = self.model(email=email, **extra_fields)
            user.set_password(password)
            user.save(using=self._db)
            return user

    def create_superuser(self, email, password=None, **extra_fields):
            extra_fields.setdefault('is_staff', True)
            extra_fields.setdefault('is_superuser', True)
            return self.create_user(email, password, **extra_fields)

    # vendas
class Venda(models.Model):
        STATUS_CHOICES = [
            ('pendente', 'Pendente'),
            ('processando', 'Processando'),
            ('concluida', 'Concluída'),
            ('cancelada', 'Cancelada'),
        ]
        
        produto = models.ForeignKey(Produto, on_delete=models.CASCADE, verbose_name="Produto")
        quantidade = models.PositiveIntegerField(validators=[MinValueValidator(1)], verbose_name="Quantidade")
        preco_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço Unitário")
        total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total")
        data_venda = models.DateTimeField(default=timezone.now, verbose_name="Data da Venda")  # Use default por enquanto
        vendedor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Vendedor")
        status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente', verbose_name="Status")
        observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
        
        class Meta:
            verbose_name = "Venda"
            verbose_name_plural = "Vendas"
            ordering = ['-data_venda']
        
        def __str__(self):
            return f"Venda #{self.id} - {self.produto.nome}"
        
        def save(self, *args, **kwargs):
            self.total = self.quantidade * self.preco_unitario
            super().save(*args, **kwargs)
