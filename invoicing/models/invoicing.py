# invoicing/models.py
from django.db import models

from sales.models.sales import Venda


class NotaFiscal(models.Model):
    venda = models.OneToOneField(Venda, on_delete=models.PROTECT, related_name="nfe")
    numero = models.CharField(max_length=20, blank=True, null=True)
    serie = models.CharField(max_length=5, default="1")
    status = models.CharField(
        max_length=20,
        choices=[
            ("pendente", "Pendente"),
            ("em_processamento", "Em processamento"),
            ("autorizada", "Autorizada"),
            ("rejeitada", "Rejeitada"),
            ("cancelada", "Cancelada"),
        ],
        default="pendente",
    )
    chave = models.CharField(max_length=44, blank=True, null=True)
    xml_autorizado = models.TextField(blank=True, null=True)
    protocolo = models.CharField(max_length=60, blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
