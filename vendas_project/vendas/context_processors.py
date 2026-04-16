# vendas/context_processors.py
from django.conf import settings

def mercadopago_settings(request):
    return {
        'MERCADOPAGO_PUBLIC_KEY': getattr(settings, 'MERCADOPAGO_PUBLIC_KEY', ''),
    }