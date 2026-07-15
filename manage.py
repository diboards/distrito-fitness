from vendas.models import Produto, ProdutoVariacao
from cloudinary.uploader import upload
import requests
from io import BytesIO

# Baixar uma imagem placeholder
img_url = "https://placehold.co/600x400?text=Produto"
response = requests.get(img_url)
img_data = BytesIO(response.content)

# Fazer upload para o Cloudinary
result = upload(img_data, folder="produtos", public_id="placeholder")
placeholder_url = result['secure_url']

print(f"Placeholder URL: {placeholder_url}")

# Adicionar imagem a produtos sem imagem
count = 0
for p in Produto.objects.all():
    if not p.imagem:
        p.imagem = placeholder_url
        p.save()
        count += 1
        print(f"✅ Imagem adicionada ao produto: {p.nome}")

print(f"Total: {count} produtos atualizados")
